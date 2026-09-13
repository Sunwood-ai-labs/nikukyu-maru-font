"""Publish completed artifacts atomically; tolerate transient Windows file locks."""
import os, time, uuid
from pathlib import Path
from io import BytesIO

def write_bytes(path, data):
    path=Path(path)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temp.write_bytes(data)
        for attempt in range(6):
            try:
                os.replace(temp,path)
                return
            except OSError:
                if attempt==5:raise
                time.sleep(.15*(attempt+1))
    finally:
        temp.unlink(missing_ok=True)

def save_png(image,path):
    buffer=BytesIO();image.save(buffer,format='PNG');write_bytes(path,buffer.getvalue())

def save_font(builder,path):
    buffer=BytesIO();builder.save(buffer);write_bytes(path,buffer.getvalue())
