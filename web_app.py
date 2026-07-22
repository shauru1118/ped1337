import os
import sys
import uuid
import base64
import threading
from pathlib import Path
from typing import Optional
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add parent directory to sys.path to resolve stego package
sys.path.insert(0, str(Path(__file__).parent))

from stego import StegoFacade, StegoError, CapacityExceededError
from stego.utils.steganalysis import perform_chi_square_analysis
import config
from tgbot import StegoBotService

app = FastAPI(
    title="Ped1337 Steganography Suite",
    description="Enterprise adaptive LSB steganography with Kuznyechik (GOST 34.12 CBC) + Zlib.",
)

# Setup directories
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "temp"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

TEMP_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Initialize StegoFacade
facade = StegoFacade()
DEFAULT_KEY_PATH = BASE_DIR / "key.key"
DEFAULT_KEY = facade.key_manager.load_or_create(str(DEFAULT_KEY_PATH))


def run_telegram_bot():
    """Runs Telegram Bot polling in a separate background thread."""
    try:
        print("Starting Telegram Bot thread...")
        bot_service = StegoBotService()
        bot_service.run()
    except Exception as e:
        print(f"Error starting Telegram Bot: {e}", file=sys.stderr)


@app.on_event("startup")
def startup_event():
    """Launches Telegram Bot thread on startup."""
    try:
        gen_path = Path("/home/shauru/.gemini/antigravity-ide/brain/0b18a14a-c961-4277-a5c9-ef660bb78820/website_avatar_1784740548319.png")
        target_path = STATIC_DIR / "avatar.png"
        if gen_path.exists():
            import shutil
            shutil.copy(str(gen_path), str(target_path))
    except Exception as e:
        print(f"Error copying avatar: {e}")

    if config.TELEGRAM_BOT_TOKEN:
        t = threading.Thread(target=run_telegram_bot, daemon=True)
        t.start()
    else:
        print("TELEGRAM_BOT_TOKEN not set. Running web interface only.")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Serves the main single page web application."""
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request},
        request=request,
    )


@app.post("/api/embed")
async def api_embed(
    cover: UploadFile = File(...),
    payload_file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    key: Optional[str] = Form(None),
):
    """Embeds text or file into cover image using adaptive LSB."""
    temp_cover = TEMP_DIR / f"web_cover_{uuid.uuid4().hex}_{cover.filename}"
    temp_payload = None
    out_stego = TEMP_DIR / f"web_stego_{uuid.uuid4().hex}.png"

    try:
        # Save cover image
        with open(temp_cover, "wb") as f:
            f.write(await cover.read())

        # Resolve encryption key
        enc_key = DEFAULT_KEY
        if key:
            try:
                enc_key = base64.b64decode(key.encode("utf-8"))
                if len(enc_key) != 32:
                    raise ValueError
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Некорректный ключ. Должен быть 32-байтовым Base64 хэшем.",
                )

        # Build envelope bytes
        if payload_file and payload_file.filename:
            temp_payload = TEMP_DIR / f"web_pay_{uuid.uuid4().hex}_{payload_file.filename}"
            payload_content = await payload_file.read()
            with open(temp_payload, "wb") as f:
                f.write(payload_content)

            envelope_bytes = facade.create_file_envelope(
                payload_file.filename, payload_content
            )
        elif text:
            envelope_bytes = facade.create_text_envelope(text)
        else:
            raise HTTPException(
                status_code=400,
                detail="Пожалуйста, введите текст или выберите файл для встраивания.",
            )

        # Run embedding
        facade.embed_encrypted(
            str(temp_cover),
            str(out_stego),
            envelope_bytes,
            enc_key,
        )

        return FileResponse(
            path=out_stego,
            filename="stego_container.png",
            media_type="image/png",
        )

    except CapacityExceededError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно места в изображении! Вмещается только {round(e.required_ratio * 100, 1)}% данных.",
        )
    except StegoError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {e}")
    finally:
        # Schedule cleanup
        def cleanup():
            for p in (temp_cover, temp_payload):
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

        threading.Timer(10, cleanup).start()


@app.post("/api/extract")
async def api_extract(
    stego: UploadFile = File(...),
    key: Optional[str] = Form(None),
):
    """Extracts and decrypts secret payload from stego container."""
    temp_stego = TEMP_DIR / f"web_extract_{uuid.uuid4().hex}_{stego.filename}"

    try:
        # Save stego image
        with open(temp_stego, "wb") as f:
            f.write(await stego.read())

        # Resolve decryption key
        dec_key = DEFAULT_KEY
        if key:
            try:
                dec_key = base64.b64decode(key.encode("utf-8"))
                if len(dec_key) != 32:
                    raise ValueError
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Некорректный ключ. Должен быть 32-байтовым Base64 хэшем.",
                )

        # Decrypt payload
        decrypted_bytes = facade.extract_decrypted(str(temp_stego), dec_key)

        # Parse envelope structure
        env_type, payload = facade.parse_envelope(decrypted_bytes)

        if env_type == "file":
            filename = payload["filename"]
            content = payload["content"]
            # Encode content to base64 for JSON response
            b64_content = base64.b64encode(content).decode("utf-8")
            return JSONResponse(
                content={
                    "type": "file",
                    "filename": filename,
                    "content": b64_content,
                }
            )
        else:
            return JSONResponse(
                content={
                    "type": "text",
                    "text": payload["text"],
                }
            )

    except StegoError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка демаскирования: {e}. Возможно, файл поврежден или введен неверный ключ.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {e}")
    finally:
        if os.path.exists(temp_stego):
            try:
                os.remove(temp_stego)
            except Exception:
                pass


@app.post("/api/visualize")
async def api_visualize(stego: UploadFile = File(...)):
    """Generates visual LSB maps and returns web URLs for them."""
    temp_stego = TEMP_DIR / f"web_vis_{uuid.uuid4().hex}_{stego.filename}"

    try:
        with open(temp_stego, "wb") as f:
            f.write(await stego.read())

        # Generate views (returns absolute / relative paths)
        views = facade.generate_visualization(str(temp_stego))

        # Copy views to static dir to make them web-accessible
        web_urls = []
        for path_str in views:
            path_obj = Path(path_str)
            if path_obj.exists():
                web_filename = f"vis_{uuid.uuid4().hex}_{path_obj.name}"
                dest = STATIC_DIR / web_filename
                dest.write_bytes(path_obj.read_bytes())
                web_urls.append(f"/static/{web_filename}")
                # Clean up local overlay temp file
                try:
                    os.remove(path_obj)
                except Exception:
                    pass

        return JSONResponse(content={"urls": web_urls})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка визуализации: {e}")
    finally:
        if os.path.exists(temp_stego):
            try:
                os.remove(temp_stego)
            except Exception:
                pass


@app.get("/api/keygen")
def api_keygen():
    """Generates a new random 256-bit AES key and returns its Base64 encoding."""
    key_bytes = facade.key_manager.generate()
    b64_key = base64.b64encode(key_bytes).decode("utf-8")
    return {"key": b64_key}


@app.post("/api/verify")
async def api_verify(
    stego: UploadFile = File(...),
    key: Optional[str] = Form(None),
):
    """Verifies the integrity/authenticity of the payload (validates GOST MAC)."""
    temp_stego = TEMP_DIR / f"web_verify_{uuid.uuid4().hex}_{stego.filename}"
    try:
        with open(temp_stego, "wb") as f:
            f.write(await stego.read())

        dec_key = DEFAULT_KEY
        if key:
            try:
                dec_key = base64.b64decode(key.encode("utf-8"))
                if len(dec_key) != 32:
                    raise ValueError
            except Exception:
                return JSONResponse(
                    content={
                        "valid": False,
                        "reason": "Некорректный формат ключа. Должен быть 32 байта Base64.",
                    }
                )

        try:
            # Attempt extraction (which triggers MAC check)
            decrypted_bytes = facade.extract_decrypted(str(temp_stego), dec_key)
            env_type, payload = facade.parse_envelope(decrypted_bytes)

            if env_type == "file":
                info = f"📦 Скрытые данные: Файл '{payload['filename']}' ({round(len(payload['content'])/1024, 2)} KB)"
            else:
                info = f"📝 Скрытые данные: Текстовое сообщение ({len(payload['text'])} символов)"

            return JSONResponse(content={"valid": True, "info": info})
        except Exception as e:
            err_msg = str(e)
            if "имитовставки" in err_msg or "decryption failed" in err_msg:
                reason = "Ошибка проверки имитовставки (данные изменены, повреждены или указан неверный ключ)"
            else:
                reason = f"Ошибка разбора контейнера: {err_msg}"
            return JSONResponse(content={"valid": False, "reason": reason})

    finally:
        if os.path.exists(temp_stego):
            try:
                os.remove(temp_stego)
            except Exception:
                pass


@app.post("/api/capacity")
async def api_capacity(cover: UploadFile = File(...)):
    """Calculates maximum embedding capacity of the cover image."""
    temp_cover = TEMP_DIR / f"web_cap_{uuid.uuid4().hex}_{cover.filename}"
    try:
        with open(temp_cover, "wb") as f:
            f.write(await cover.read())

        cap = facade.calculate_capacity(str(temp_cover))
        return JSONResponse(content=cap)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_cover):
            try:
                os.remove(temp_cover)
            except Exception:
                pass



@app.post("/api/steganalysis")
async def api_steganalysis(image: UploadFile = File(...)):
    """Performs multi-channel LSB steganalysis with Chi-Square and Shannon Entropy."""
    temp_img = TEMP_DIR / f"web_stegoan_{uuid.uuid4().hex}_{image.filename}"
    try:
        with open(temp_img, "wb") as f:
            f.write(await image.read())

        img_array = facade.engine.image_adapter.load(str(temp_img))
        analysis_data = perform_chi_square_analysis(img_array, num_points=50)
        
        final_p_red = analysis_data["red"]["p_values"][-1]
        final_p_green = analysis_data["green"]["p_values"][-1]
        final_p_blue = analysis_data["blue"]["p_values"][-1]
        
        final_e_red = analysis_data["red"]["entropies"][-1]
        final_e_green = analysis_data["green"]["entropies"][-1]
        final_e_blue = analysis_data["blue"]["entropies"][-1]
        
        max_p_rgb = max(final_p_red, final_p_green, final_p_blue)
        avg_p_rgb = (final_p_red + final_p_green + final_p_blue) / 3.0
        max_e_rgb = max(final_e_red, final_e_green, final_e_blue)
        avg_e = (final_e_red + final_e_green + final_e_blue) / 3.0
        
        # Steganography detection criteria
        if max_e_rgb >= 0.994 and max_p_rgb >= 0.3:
            verdict = "detected"
        elif max_e_rgb >= 0.98 or max_p_rgb >= 0.1:
            verdict = "anomaly"
        else:
            verdict = "clean"
            
        return JSONResponse(content={
            "results": analysis_data,
            "verdict": verdict,
            "max_entropy": max_e_rgb,
            "avg_entropy": avg_e,
            "max_p": max_p_rgb,
            "avg_p": avg_p_rgb
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка стегоанализа: {e}")
    finally:
        if os.path.exists(temp_img):
            try:
                os.remove(temp_img)
            except Exception:
                pass



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run("web_app:app", host="0.0.0.0", port=port, reload=True)
