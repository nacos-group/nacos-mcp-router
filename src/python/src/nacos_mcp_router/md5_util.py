#-*- coding: utf-8 -*-
import hashlib

def get_md5(text: str) -> str:
    text_bytes = text.encode('utf-8')
    md5_hash = hashlib.md5(text_bytes)
    return md5_hash.hexdigest()