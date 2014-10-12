#!python3.4
from urllib.request import urlopen
from PIL.ImageGrab import grab
from pymouse import PyMouse
from msvcrt import getch
from io import BytesIO
from PIL import Image
import random
import math
import time


class picture:

	def __init__(self, filename, source, scale):
		self.name = filename
		self.source = source
		self.scale = scale

	def load(self):
		rgb = [[0,0,0,0,i,0] for i in range(64)]
		if self.source==1:
			im = Image.open(self.name)
		else:
			fd = urlopen(self.name)
			image_file = BytesIO(fd.read())
			im=Image.open(image_file)
		im = im.convert('RGBA')
		width, height = im.size
		rec = [[-1 for x in range(width)] for y in range(height)]
		pixdata = [[(0,0,0,0) for x in range(width)] for y in range(height)]
		totalpix=0
		print('Loading picture, please wait')
		for y in range(height):
			if y==height//2:
				print('Analyzing picture')
			for x in range(width):
				r,g,b,a = im.getpixel((x,y))
				pixdata[y][x] = r,g,b,a
				if a>128:
					totalpix+=1
					ind = (r//64)*16 + (g//64)*4 + b//64
					rgb[ind][0]+=r
					rgb[ind][1]+=g
					rgb[ind][2]+=b
					rgb[ind][3]+=1
					rec[y][x]=ind
		avecolor=[]
		for i in range(64):
			if rgb[i][3]==0:
				avecolor.append([-1,-1,-1])
			else:
				avecolor.append([rgb[i][0]//rgb[i][3],rgb[i][1]//rgb[i][3],rgb[i][2]//rgb[i][3]])
		srgb = sorted(rgb, key = lambda foo: -foo[3])
		pixcount = 0
		maxcolor=9
		for i in range(9):
			pixcount += srgb[i][3]
			if pixcount > 0.8*totalpix:
				maxcolor=i+1
				break
		while True:
			alist=[]
			los = 1 - pixcount/totalpix
			for ind in range(maxcolor-1):
				alist.append(srgb[ind][4])
			r1,g1,b1,n1=0,0,0,0
			for ind in range(maxcolor-1,64):
				r1+=srgb[ind][0]
				g1+=srgb[ind][1]
				b1+=srgb[ind][2]
				n1+=srgb[ind][3]
			if n1>0:
				r1 = r1//n1
				g1 = g1//n1
				b1 = b1//n1
			im1 = Image.new('RGBA',(width,height))
			pixcount=0
			segcount=0
			print('With {} different colors, recovery rate is {:.2%}'.format(maxcolor, 1-los))
			for y in range(height):
				if y==height//2:
					print('The output picutre will look like this:')
				oldc=-1
				for x in range(width):
					if rec[y][x]==-1:
						im1.putpixel((x,y),(255,255,255,0))
						newc=rec[y][x]
					elif rec[y][x] in alist:
						r,g,b = avecolor[rec[y][x]]
						im1.putpixel((x,y),(r,g,b,255))
						newc=rec[y][x]
					else:
						im1.putpixel((x,y),(r1,g1,b1,255))
						newc=100
					if newc!=oldc:
						if oldc!=-1:
							segcount+=1
						oldc=newc
				if oldc!=-1:
					segcount+=1
			im1.show()
			estm = segcount//500 + (width*height*self.scale)//200000
			print('Estimated painting time is {} minutes.'.format(estm))
			print('Improve output image quanlity (y/n)?')
			while True:
				c=getch().decode()
				if c=='n' or c=='y':
					break
			if c=='n':
				break
			pixcount=0
			for i in range(64):
				pixcount+=srgb[i][3]
				if pixcount > totalpix*(1-los/2):
					break
			maxcolor = i+1
		print('Ready to paint, press any key to start.')
		c=getch().decode()
		if c=='e':
			input()
		palette=[]
		for i in range(maxcolor-1):
			n = srgb[i][4]
			r,g,b = avecolor[n]
			palette.append((n,r,g,b))
		palette.append((-1,r1,g1,b1))
		return pixdata, palette

	def crop(self, pixdata, start_x, start_y, end_x, end_y):
		pixblock = [[(255,255,255,255) for x in range(end_x-start_x)] for y in range(end_y-start_y)]
		for y in range(start_y,end_y):
			for x in range(start_x,end_x):
				pixblock[y-start_y][x-start_x] = pixdata[y][x]
		return pixblock
		
	def parse(self, pixblock, palette, ind):
		segments=[]
		height=len(pixblock)
		width=len(pixblock[0])
		num,red,green,blue=palette[ind]
		for j in range(height):
			flag = 0
			for i in range(width):
				r,g,b,a = pixblock[j][i]
				if (num<0 or (r//64)*16+(g//64)*4+(b//64)==num) and a>150:
					pixblock[j][i] = (0,0,0,0)
					if flag==0:
						flag = 1
						xl = i
				else:
					if flag==1:
						flag=0
						xr = i-1
						segments.append((j,xl,xr))
			if flag==1:
				xr=i
				segments.append((j,xl,xr))
		return segments, pixblock


class paint:	
	
	def __init__(self, mouse, saveink=False):
		self.mouse = mouse
		self.saveink = saveink
		self.scr_width, self.scr_height = mouse.screen_size()
		self.center_x = 170 + self.scr_width//2
		self.center_y = self.scr_height//2
		if self.scr_width==1280 or self.scr_width==1366:
			self.wheel_x = 502 + self.scr_width//2
			self.wheel_y = 212 + self.scr_height//2
			self.radius = 31
		else:
			self.wheel_x, self.wheel_y, self.radius = 0,0,0
	
	def shift(self, dir, t):
		if dir == 'up':
			self.mouse.move(self.center_x, self.center_y - 318)
		elif dir == 'down':
			self.mouse.move(self.center_x, self.center_y + 318)
		elif dir == 'left':
			self.mouse.move(self.center_x - 318, self.center_y)
		elif dir == 'right':
			self.mouse.move(self.center_x + 318, self.center_y)
		time.sleep(t)
		self.mouse.move(self.center_x, self.center_y)

	def drift(self, dir, t, x0, y0, vec1, vec2):
		self.shift(dir,t)
		time.sleep(3)
		self.mouse.move(1,1)
		im = grab()
		data = [sum(im.getpixel((x0+k*vec1, y0+k*vec2))[:3]) for k in range(409)]
		for k in range(401):
			if data[k] < 100:
				if max(data[k+1:k+3])>650 and min(data[k+2:k+5])<100 and max(data[k+3:k+6])>650 and min(data[k+4:k+7])<100:
					return k
		return -1

	def drawcircle(self, x, y, r):
		self.mouse.press(x+r,y)
		for degree in range(361):
			theta = 2*math.pi*degree/360
			self.mouse.drag(x+round(r*math.cos(theta)), y+round(r*math.sin(theta)))
			time.sleep(0.01)
		time.sleep(0.1)
		self.mouse.release(x+r,y)
	
	def setmouse(self):
		print('I need more information about your screen size.')
		print('Please set pen size to 1 and choose a color that is not on the ball.')
		print('Please use asdw keys to put the mouse near the center of the big ball, then press enter, I will help you to find the center.')
		x=self.center_x
		y=self.center_y
		m = self.mouse
		while True:
			c=getch().decode()
			if c=='a':
				x-=1
			elif c=='d':
				x+=1
			elif c=='w':
				y-=1
			elif c=='s':
				y+=1
			elif c=='\r' or c=='\n':
				r=320
				self.drawcircle(x,y,300)
				self.drawcircle(x,y,320)
				self.drawline(x-r,y,x-r+20,y)
				self.drawline(x+r-20,y,x+r,y)
				self.drawline(x,y-r+20,x,y-r)
				self.drawline(x,y+r-20,x,y+r)
				self.drawline(x-20,y,x+20,y)
				self.drawline(x,y-20,x,y+20)
				print('Is the pen in the center of the ball now(y/n)?')
				c=getch().decode()
				if c=='y':
					break
				elif c=='n':
					print('Please use asdw keys to put the mouse near the center of the big ball, then press enter, I will help you to find the center.')
					continue
			self.mouse.move(x,y)
		self.center_x = x
		self.center_y = y
		x = 502 + self.scr_width//2
		y = 212 + self.scr_height//2
		print('Please use asdw keys to put the mouse near the center of the color wheel, then press enter.')
		while True:
			c=getch().decode()
			if c=='a':
				x-=1
			elif c=='d':
				x+=1
			elif c=='w':
				y-=1
			elif c=='s':
				y+=1
			elif c=='\r' or c=='\n':
				break
			self.mouse.move(x,y)
		self.mouse.click(x,y-15)
		time.sleep(0.1)
		im=grab()
		maxr = 0
		maxj = 0
		cx = 0
		lv=0
		for j in range(-8,9):
			data=[sum(im.getpixel((x-50+k,y+j))) for k in range(100)]
			left, right = -1,0
			for k in range(100):
				if data[k]<60:
					if left<0:
						left=k
					elif k-left>10:
						right=k
						break
			radius = right-left
			if radius>maxr:
				maxr=radius
				maxj = j
				cx=(left+right+1)//2
			elif radius==maxr:
				lv+=1
		x += cx-50
		y += maxj+lv//2
		self.mouse.click(x+15,y)
		time.sleep(0.1)
		im=grab()
		data=[sum(im.getpixel((x,y+j-40))) for j in range(81)]
		top,bottom=-1,-1
		for k in range(40):
			if data[40-k]<300:
				if top<0:
					top=k
			if data[40+k]<200:
				if bottom<0:
					bottom=k
		y = y+(bottom-top)//2
		self.mouse.click(x,y)
		radius = (top+bottom)//2
		return x,y,radius

	def setcolor(self, r, g, b, rainbow=0):
		if self.wheel_x == 0:
			self.wheel_x, self.wheel_y, self.radius = self.setmouse()
		wheel_x = self.wheel_x
		wheel_y = self.wheel_y
		wheel_r = self.radius
		bar_x = self.wheel_x+wheel_r+15
		if rainbow == 1:
			xt = wheel_x + round(wheel_r*math.cos(2*math.pi*r))
			yt = wheel_y - round(wheel_r*math.sin(2*math.pi*r))
			self.mouse.click(xt,yt)
			self.mouse.click(bar_x,wheel_y)
			return
		r,g,b = r/255, g/255, b/255
		maxc = max(r, g, b)
		minc = min(r, g, b)
		z = (maxc+minc)/2
		if minc == maxc:
			x,y,xn,yn = 0,0,0,0
		else:
			sc = (maxc-minc)/math.sqrt(r*r+g*g+b*b-r*g-g*b-b*r)
			x = (r - g/2 - b/2) * sc
			y = (math.sqrt(3)/2) * (g-b) * sc
			rd = math.sqrt(x*x+y*y)
			rn = math.sqrt(rd)
			xn = x/rn
			yn = y/rn
		if x>0:
			xt = wheel_x + math.floor(wheel_r*xn)
		else:
			xt = wheel_x + math.ceil(wheel_r*xn)
		if y>0:
			yt = wheel_y - math.floor(wheel_r*yn)
		else:
			yt = wheel_y - math.ceil(wheel_r*yn)
		zt = wheel_y + wheel_r - round(2*wheel_r*z)
		self.mouse.click(xt,yt)
		self.mouse.click(bar_x,zt)

	def drawline(self, startx, starty, endx, endy):
		self.mouse.press(startx, starty)
		self.mouse.drag(endx, endy)
		time.sleep(0.1)
		self.mouse.release(endx, endy)
		if self.saveink==True and (abs(endx-startx) > 40 or abs(endy-starty)>40):
			self.mouse.click(endx,endy)
			time.sleep(0.1)

	def barcode(self, startx, starty, dirx, diry, norx, nory, clean=False, color=(0,0,0)):
		barnum = 10
		barlen = 14
		barpos=-2
		if clean == False:
			im=grab()
			r,g,b=im.getpixel((startx,starty))
			barnum = 9
			barlen = 12
			barpos=0
		for i in range(barnum):
			if clean==True:
				r,g,b=color
				self.setcolor(r,g,b)
			else:
				col = 255*((i%4)//2)
				self.setcolor(col,col,col)
			self.drawline(startx+norx*i+dirx*barpos, starty+nory*i+diry*barpos, startx+norx*i+dirx*barlen, starty+nory*i+diry*barlen)
			time.sleep(0.1)
		return r,g,b
		
	def drawblock(self, segments, startx, starty, red, green, blue, scale=2):
		if len(segments)>0:
			self.setcolor(red,green,blue)
		for seg in segments:
			y,xl,xr = seg
			self.drawline(startx+scale*xl, starty+scale*y, startx+scale*xr, starty+scale*y)

	def relocate(self, x, y, type):
		print('Use asdw to move the mouse to where the barcode should be.')
		while True:
			c=getch().decode()
			if c=='a':
				x-=1
			elif c=='d':
				x+=1
			elif c=='w':
				y-=1
			elif c=='s':
				y+=1
			elif c=='j':
				self.shift('left',1)
			elif c=='l':
				self.shift('right',1)
			elif c=='i':
				self.shift('up',1)
			elif c=='k':
				self.shift('down',1)
			elif c=='\r' or c=='\n':
				break
			self.mouse.move(x,y)
		if type==0:
			self.barcode(x,y,0,1,1,0)
		elif type==1:
			self.barcode(x,y,1,0,0,1)
			self.barcode(x,y,0,-1,-1,0)
		return x,y

	def autodraw(self, filename, source, scale=2):
		pic = picture(filename, source, scale)
		pixdata,palette = pic.load()
		height = len(pixdata)
		width = len(pixdata[0])
		cnum = len(palette)
		xr, yr = 0, 0
		ulx, uly = 0, 0
		self.setcolor(255,255,255)
		time.sleep(1)
		safec = 5
		while True:
			ulx=0
			shiftcount = 0
			while True:
				shiftcount += 1
				if ulx>0:
					self.barcode(self.center_x+xr+safec-200, self.center_y-5,0,1,1,0, clean=True, color=(r1,g1,b1))
				if ulx+(400-xr)//scale < width:
					self.mouse.move(self.center_x, self.center_y)
					r1,g1,b1 = self.barcode(self.center_x+200+safec,self.center_y-5,0,1,1,0)
				if ulx==0:
					if uly>0:
						self.barcode(self.center_x+xr-safec-201, self.center_y+yr+safec-200,1,0,0,1, clean=True, color=(r2,g2,b2))
						self.barcode(self.center_x+xr-safec-201, self.center_y+yr+safec-200,0,-1,-1,0, clean=True, color=(r2,g2,b2))
					if uly+(400-yr)//scale < height:
						r2,g2,b2 = self.barcode(self.center_x+xr-201-safec, self.center_y+safec+200,1,0,0,1)
						self.barcode(self.center_x+xr-201-safec, self.center_y+safec+200,0,-1,-1,0)
				sx = max(ulx-1,0)
				sy = max(uly-1,0)
				ex = min(1+ulx+(400-xr)//scale, width-1)
				ey = min(1+uly+(400-yr)//scale, height-1)
				pixblock = pic.crop(pixdata,sx,sy,ex,ey)
				for ind in range(cnum):
					seg,pixblock = pic.parse(pixblock, palette, ind)
					red,green,blue = palette[ind][1:]
					self.drawblock(seg, self.center_x+xr-200, self.center_y+yr-200, red, green, blue, scale)
				time.sleep(0.5)
				ulx = ulx + (400-xr)//scale
				if ulx>=width:
					break
				xr = self.drift('right', 1, self.center_x-200, self.center_y, 1, 0)
				if xr<0:
					input('Lost target')
					xt,yt = self.relocate(self.center_x, self.center_y, 0)
					xr = xt - self.center_x + 200
				while xr >= 100:
					xr = self.drift('right', xr/400, self.center_x-200, self.center_y, 1, 0)
					while xr<=0:
						xr = self.drift('left', 0.5, self.center_x-200, self.center_y, 1, 0)
				xr-=safec
			uly = uly + (400-yr)//scale
			if uly>=height:
				break
			xr = self.drift('left', 2, self.center_x+199, self.center_y+200, -1, 0)
			cnt = 0
			while xr==-1:
				xr = self.drift('left', 1, self.center_x+199, self.center_y+200, -1,0)
				cnt+=1
				if cnt>=shiftcount+2:
					print('Lost target')
					xt,yt = self.relocate(self.center_x, self.center_y, 1)
					xr = self.center_x + 200 - xt
			while xr<=300:
				xr = self.drift('right', (400-xr)/400, self.center_x+199, self.center_y+200, -1,0)
				while xr<0:
					xr = self.drift('left', 0.5, self.center_x+199, self.center_y+200, -1,0)
			xr = 400-xr
			xr+=safec
			yr = self.drift('down', 1, self.center_x+xr-200, self.center_y-200, 0, 1)
			while yr >= 100:
				yr = self.drift('down', yr/400, self.center_x+xr-200, self.center_y-200, 0, 1)
				while yr<=0:
					yr = self.drift('up', 0.5, self.center_x+xr-200, self.center_y-200, 0, 1)
			yr-=safec

#main
m=PyMouse()
while True:
	print('*'*30)
	print('      PigScript v1.4')
	print('*'*30)
	print('Press 1 for local pictures, press 2 for website pictures:')
	while True:
		c=getch().decode()
		if c=='1' or c=='2':
			source = int(c)
			break
	if source==1:
		filename = input('Picture name: ')
	else:
		filename = input('URL of the picture: ')
	print('Enter your pen size (1-9): ')
	while True:
		c=getch().decode()
		if c in '0123456789':
			break
	sc = int(c)
	print('Please manually set your pen size to', c)
	print('Press s to ensable ink-saving mode (it will paint slower though)')
	c=getch().decode()
	svnk = False
	if c=='s':
		svnk = True
	pen = paint(m,saveink=svnk)
	tm = time.clock()
	pen.autodraw(filename, source, sc)
	sec = int(time.clock()-tm)
	print('Time elapsed {} minutes {} seconds'.format(sec//60, sec%60))
