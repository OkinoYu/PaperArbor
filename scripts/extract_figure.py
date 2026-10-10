#!/usr/bin/env python3
"""Render a PDF page crop to a bounded, lossless PNG (optional PDF dependencies)."""
import argparse
from pathlib import Path

def extract(pdf, page, box, output, width=1600):
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError('Install optional dependencies: python3 -m pip install -r requirements-figures.txt') from exc
    if output.exists(): raise FileExistsError('refusing to overwrite figure')
    with pdfplumber.open(pdf) as doc:
        if not 1<=page<=len(doc.pages):raise ValueError('page is 1-based and must be inside PDF')
        p=doc.pages[page-1]
        if box is not None:
            x0,y0,x1,y1=box
            if not 0<=x0<x1<=p.width or not 0<=y0<y1<=p.height:raise ValueError('invalid crop rectangle in PDF points')
            p=p.crop(tuple(box))
        im=p.to_image(resolution=180).original.convert('RGB')
        if im.width>width:
            from PIL import Image
            im.resize((width,round(im.height*width/im.width)),Image.Resampling.LANCZOS).save(output,'PNG',optimize=True)
        else:im.save(output,'PNG',optimize=True)
    return output.stat().st_size

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pdf',type=Path);p.add_argument('--page',type=int,required=True);p.add_argument('--box',type=float,nargs=4,metavar=('X0','Y0','X1','Y1'));p.add_argument('--width',type=int,default=1600);p.add_argument('-o','--output',type=Path,required=True);a=p.parse_args()
    if not 200<=a.width<=2400:p.exit(1,'width must be 200..2400\n')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    print(f'{extract(a.pdf,a.page,a.box,a.output,a.width)} bytes -> {a.output}')
if __name__=='__main__':main()
