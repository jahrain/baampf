#!/usr/bin/env python

import os
import sys
from fnmatch import fnmatch
import id3
from PIL import Image

MAX_IMAGE_SIZE = 1024

def is_image_file(filename):
   exts = ['.jpg', '.jpeg', '.png']
   for ext in exts:
       if fnmatch(filename.lower(), "*"+ext):
           return True
   return False

def cover_rating(filename, directory):
    parent_dirname = os.path.basename(directory).lower()
    names = {
        parent_dirname: 1.0,
        'cover': 1.0,
        'albumart': 0.75,
        'folder':0.75,
        'img_0001':0.5,
        'image':0.5,
    }
    score = 0
    for n in names:
        if n in filename.lower():
            score += names[n]
    return score

def process_image_ratios(path):
    filelist = []
    for dirname, dirnames, filenames in os.walk(path):
        print dirname
        for f in filenames:
            if not is_image_file(f):
                continue
            if fnmatch(f,'*.right.*') or fnmatch(f,'*.left.*'):
                os.remove(os.path.join(dirname,f))
            else:
                filelist.append(os.path.join(dirname,f))
    for f in filelist:
        im = Image.open(f)
        ratio = float(im.size[0])/float(im.size[1])
        if ratio > 1.8:
            print f
            right = im.crop((im.size[0]/2,0,im.size[0],im.size[1]))
            if right.size[0] > 1024:
                right = right.resize((right.size[0]/2,right.size[1]/2),Image.ANTIALIAS)
            right.save(f + '.right.jpg')
            left = im.crop((0,0,im.size[0]/2,im.size[1]))
            if left.size[0] > 1024:
                left = left.resize((left.size[0]/2,left.size[1]/2),Image.ANTIALIAS)
            left.save(f + '.left.jpg')
        elif im.size[0] > MAX_IMAGE_SIZE:
            small = im.resize((1024,1024*im.size[1]/im.size[0]),Image.ANTIALIAS)
            small.save(f + '.small.jpg')
            

def find_cover_art(path):
    image_files = []
    for dirname, dirnames, filenames in os.walk(path):
        for f in filenames:
            if not is_image_file(f):
                continue

            full_path = os.path.join(dirname, f)
            image_files.append((cover_rating(f, dirname), full_path))

            """if fnmatch.fnmatch(f.lower(),'*.jpg') or fnmatch.fnmatch(f.lower(),'*.png'):
                if fnmatch.fnmatch(f.lower(),'cover.*') or \
                    'albumart' in f.lower() or \
                    'cover' in f.lower() or \
                    'folder' in f.lower() or \
                    'img_0001' in f.lower():
                        return os.path.join(dirname, f)"""
    """for dirname, dirnames, filenames in os.walk(path):
        for f in filenames:
            if fnmatch.fnmatch(f.lower(),'*.jpg') or fnmatch.fnmatch(f.lower(),'*.png'):
                return os.path.join(dirname, f)"""
    if not len(image_files):
        return None

    image_files.sort(key=lambda tup: tup[0])
    return image_files[-1][1]

def find_mp3s(path):
    mp3s = []
    for dirname, dirnames, filenames in os.walk(path):
        for f in filenames:
            if fnmatch(f.lower(),'*.mp3'):
                mp3s.append(os.path.join(dirname, f))
    return mp3s

def apply_cover_art(path):
    for d in os.listdir(path):
        full_path = os.path.join(path,d)
        if not os.path.isdir(full_path):
            continue
        cover_art = find_cover_art(full_path)       
        if not cover_art:
            continue
        print "Applying album artwork:", full_path, cover_art
        mp3s = find_mp3s(full_path)
        
        for mp3 in mp3s:
            found_apic = False
            try:
                #id3v1 = id3.ID3v1(mp3)
                id3v2 = id3.ID3v2(mp3)
            except:
                continue
            for frame in id3v2.frames:
                if frame.id == 'APIC':
                    found_apic = True
                    break
            changed = False
            if not found_apic:
                print mp3, "NO APIC"
                newframe = id3v2.new_frame('APIC')
                ext = os.path.splitext(cover_art)[1].lower()
                
                if ext in [".jpg",".jpeg"]:
                    newframe.mimetype = "image/jpeg"
                elif ext == ".png":
                    newframe.mimetype = "image/png"
                newframe.picturetype = '\x03'
                im = Image.open(cover_art)
                tmp_cover_art = cover_art
                if os.path.exists(cover_art + ".small"+ext):
                    tmp_cover_art = cover_art + ".small"+ext
                elif im.size[0] > MAX_IMAGE_SIZE*1.2:
                    print " -> resize", cover_art
                    tmp_cover_art = cover_art + ".small"+ext
                    ratio = float(im.size[0])/float(im.size[1])
                    small = im.resize((
                        MAX_IMAGE_SIZE,
                        MAX_IMAGE_SIZE*im.size[1]/im.size[0]),
                        Image.ANTIALIAS)
                    small.save(tmp_cover_art)
                     
                newframe.image = open(tmp_cover_art, 'rb').read()
                print " -> Applying", tmp_cover_art, "to", mp3
                changed = True

            found_tpe2 = False
            for frame in id3v2.frames:
                if frame.id == 'TPE2':
                    found_tpe2 = True
                    break
                
            if not found_tpe2:
                newframe = id3v2.new_frame('TPE2')
                newframe.set_value("Various Artists")
                print " -> apply TPEC 'Various Artists' to", mp3
                changed = True
                
            if changed:
                id3v2.unsync = 0
                id3v2.save()

if __name__ == '__main__':
    apply_cover_art(sys.argv[1])
