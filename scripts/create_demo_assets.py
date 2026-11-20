"""Generate non-commercial test assets for validating Gumroad file delivery."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import math
import struct
import wave

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/"test-assets"
OUT.mkdir(exist_ok=True)
cover=OUT/"Test_Track_Cover_DEMO.png"
tab=OUT/"Test_Track_Guitar_Tab_DEMO.pdf"
audio=OUT/"Test_Track_Backing_Track_DEMO.wav"

# Generated from scratch: never use an existing recording or transcription.
im=Image.new("RGB",(1200,1200),(240,232,216))
d=ImageDraw.Draw(im)
d.ellipse((-370,-660,840,530),fill=(245,238,226))
d.ellipse((790,-440,1550,360),fill=(192,145,95))
d.ellipse((-520,680,1080,1800),fill=(199,157,112))
d.ellipse((300,800,1550,1850),fill=(44,43,42))
try:
    title=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",68)
    sub=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",26)
except OSError:
    title=ImageFont.load_default();sub=title
d.text((600,470),"TEST TRACK",font=title,anchor="mm",fill=(35,34,32))
d.line((480,530,720,530),fill=(167,113,71),width=5)
d.text((600,590),"SIMON LIBON",font=sub,anchor="mm",fill=(42,42,41))
d.text((600,1112),"DEMO  /  NOT FOR SALE",font=sub,anchor="mm",fill=(240,230,211))
im.save(cover,optimize=True)

c=canvas.Canvas(str(tab),pagesize=A4)
w,h=A4
c.setFont("Helvetica-Bold",24);c.drawString(55,h-75,"TEST TRACK")
c.setFont("Helvetica",11);c.drawString(55,h-99,"SIMON LIBON  |  ORIGINAL DEMO TAB")
c.setFont("Helvetica",10);c.drawString(55,h-140,"Standard tuning E A D G B e   |   4/4   |   100 BPM")
notes={
 "C":[(5,3),(3,0),(2,1),(1,0),(5,3),(3,0),(2,1),(1,0)],
 "Am":[(5,0),(3,2),(2,1),(1,0),(5,0),(3,2),(2,1),(1,0)],
 "Fmaj7":[(4,3),(3,2),(2,1),(1,0),(4,3),(3,2),(2,1),(1,0)],
 "G":[(6,3),(3,0),(2,0),(1,3),(6,3),(3,0),(2,0),(1,3)]}
for system in range(2):
    y=h-220-system*170
    for string,label in enumerate(("e","B","G","D","A","E")):
        yy=y-string*13
        c.setLineWidth(.5);c.line(60,yy,w-50,yy)
        c.setFont("Helvetica",8);c.drawRightString(55,yy-3,label)
    bw=(w-110)/4
    for bar,name in enumerate(("C","Am","Fmaj7","G")):
        left=60+bar*bw
        c.setFont("Helvetica-Bold",10);c.drawString(left+8,y+24,name)
        c.line(left,y+8,left,y-66)
        for idx,(string,fret) in enumerate(notes[name]):
            x=left+9+idx*(bw-15)/8
            yy=y-(string-1)*13
            c.setFillColorRGB(1,1,1);c.rect(x-2,yy-5,12,10,fill=1,stroke=0)
            c.setFillColorRGB(0,0,0);c.setFont("Courier-Bold",9);c.drawString(x,yy-3,str(fret))
    c.line(w-50,y+8,w-50,y-66)
c.setFont("Helvetica-Bold",12);c.drawString(55,220,"TEST ONLY - DO NOT PUBLISH OR SELL")
c.setFont("Helvetica",10);c.drawString(55,200,"This is an original synthetic example, not a real music release.")
c.drawString(55,183,"Prepared solely to verify the file delivery and shop integration.")
c.save()

sr=16000
bpm=100
beat=60.0/bpm
bar=4*beat
chords=[
 (130.8128,[261.6256,329.6276,392.0]),
 (110.0,[220.0,261.6256,329.6276]),
 (87.307,[174.614,261.6256,329.6276]),
 (97.999,[195.998,246.9417,391.9954])]
with wave.open(str(audio),"wb") as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
    # Four original chord backing bars with a subtle click: no lead guitar.
    for idx,(root,tones) in enumerate(chords):
        frame=bytearray()
        for n in range(round(sr*bar)):
            t=n/sr
            fade=min(1,t/.06,max(0,(bar-t)/.15))
            chord=sum(math.sin(2*math.pi*hz*t) for hz in tones)/len(tones)
            pad=.22*chord*fade
            b=t%beat
            pulse=(.06 if int(t/beat)==0 else .035)*math.sin(2*math.pi*root*t)*math.exp(-b*9)
            click=.012*math.sin(2*math.pi*900*b)*math.exp(-b*70)
            sample=max(-1,min(1,pad+pulse+click))
            frame.extend(struct.pack("<h",round(sample*32767)))
        f.writeframes(frame)
print("Generated",[(p.name,p.stat().st_size) for p in (cover,tab,audio)])
