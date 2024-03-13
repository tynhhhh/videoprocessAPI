from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import List, Tuple
from func import APIfunction
import models, os
from database import engine, SessionLocal
from sqlalchemy import select
from models import OrginalVideos
from datetime import datetime
import uuid

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

func = APIfunction()
database_folder = func.database_folder

async def write_content(file):
    video_content = await file.read()

    file_name = file.filename
    file_path = os.path.join(database_folder,file_name)

    with open(file_path, "wb") as f:
        f.write(video_content)
        f.close()
    return file_path

@app.get("/videos")
def get_videos():
    db = SessionLocal()
    try:
        query = select(OrginalVideos)
        data = db.execute(query).scalars().all()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()


@app.post("/videos/upload")
async def upload_video(file: UploadFile=File(...)):
    video_contents = await file.read()
    videos_db = os.path.join(database_folder, "OriginalVideos")
    os.makedirs(videos_db, exist_ok=True)
    filename = f"{file.filename}"
    file_path = os.path.join(videos_db, filename)

    with open(file_path, "wb") as f:
        f.write(video_contents)
    db = SessionLocal()
    try:
        video = OrginalVideos(file_path=file_path)
        db.add(video)
        db.commit()
        return HTTPException(status_code=200, detail=file_path)
    finally:
        db.close()

@app.post("/videos/cut")
async def cut_api(files: UploadFile = File(...), dur: int = Form(...)):
    file_path = await write_content(files)

    path = func.Cut(file_path,dur)
    os.remove(file_path)
    if not path:
        return HTTPException(status_code=400, detail="error!")
    return HTTPException(status_code=400, detail=path)

@app.post("/videos/insert-logo")
async def logo_api(file: UploadFile = File(...),logo: UploadFile = File(...),position:int = 1):
    file_path = await write_content(file)
    logo_path = await write_content(logo)

    path = func.InsertLogo(file_path, logo_path, position)
    os.remove(file_path)
    os.remove(logo_path)
    return HTTPException(status_code=200, detail=path)

@app.post("/videos/concat")
async def ConcatVideos(target_platform: int = 0, files: Tuple[UploadFile,...] = File(...)):
    path_container = []
    for file in files:
        file_path = await write_content(file)
        path_container.append(file_path)
    path = func.videoConcat(target_platform, path_container)
    try:
        for p in path_container:
            os.remove(p)
    except:
        pass
    return HTTPException(status_code=200, detail=path)

@app.post("/videos/blurr")
async def BlurVideos(file: UploadFile = File(...), blur_strength: int = 15, num_jobs: int = -1):
    file_path = await write_content(file)
    path = func.BluringVideo(file_path, blur_strength, num_jobs)
    try:
        os.remove(file_path)
    except:
        pass
    return HTTPException(status_code=200, detail= path)

@app.post("/videos/speedchange")
async def SpeedChange(file: UploadFile = File(...), speed_factor: int = 2):
    file_path = await write_content(file)
    print(file_path)
    path = func.ChangingSpeed(file_path, speed_factor)
    try:
        os.remove(file_path)
    except:
        pass
    return HTTPException(status_code=200, detail= path)

@app.get("/videos/{id}")
async def get_video(id: int):
    db = SessionLocal()
    try:
        query = select(OrginalVideos).where(OrginalVideos.id == id)
        data = db.execute(query).scalar_one()
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail="Data not found")
    finally:
        db.close()