import pygame
import os

ttffonts = {
    'dejavu': ['DejaVuSerif','DejaVuSans-Bold','DejaVuSans', 'DejaVuSansMono'],
    'droid': ['DroidSans', 'DroidSans-Bold', 'DroidSerif-Regular', 'DroidSerif-Bold']
}

class pitft:
    def __init__(self):
        os.putenv('SDL_FBDEV', '/dev/fb1')
        print('init pygame')
        pygame.init()
        pygame.mouse.set_visible(False)
        print('init font')
        pygame.font.init()
        self.screen = pygame.display.set_mode((240, 320), 0, 32)
        self.screen.fill((0, 0, 0))
        print('initial lcd update')
        pygame.display.update()
 
    def font(self, fsz, fontfamily, font):
        return pygame.font.Font('/usr/share/fonts/truetype/' + fontfamily + '/' + font + '.ttf', fsz)

    def text(self, dfont, text, fx, fy, color = (255,255,255)):
      text_surface = dfont.render(text, False, color)
      self.screen.blit(text_surface, (fx, fy))

    def btext(self, dfont, text, rect, justify = 'center', color=(255,255,255)):
      (bx, by, bw, bh) = rect
      text_surface = dfont.render(text, False, color)
      tw = text_surface.get_width()
      if text_surface.get_width() > bw:
        print('err: text wider than rect')
        return
      if text_surface.get_height() > bh:
        print(text_surface.get_height(), bh, text)
        print('error: text higher than rect')
        return
      if justify == 'center':
        xoff = int((bw - text_surface.get_width()) / 2)
        yoff = int((bh - text_surface.get_height()) / 2)
      if justify == 'top':
        xoff = int((bw - text_surface.get_width()) / 2)
        yoff = 0
      elif justify =='bottom':
        xoff = int((bw - text_surface.get_width()) / 2)
        yoff = bh - text_surface.get_height()
      elif justify == 'left':
        xoff = 0
        yoff = int((bh - text_surface.get_height()) / 2)
      elif justify == 'right':
        xoff = bw - text_surface.get_width()
        yoff = int((bh - text_surface.get_height()) / 2)
      self.screen.blit(text_surface, (bx + xoff, by + yoff))

    def rtext(self, dfont, text, fy, pad = 5, color = (255,255,255)):
        text_surface = dfont.render(text, False, color)
        self.screen.blit(text_surface, (240-text_surface.get_width() - pad, fy))

    def ctext(self, dfont, text, fy, color = (255,255,255)):
        text_surface = dfont.render(text, False, color)
        xpos = int((240 - text_surface.get_width()) / 2)
        self.screen.blit(text_surface, (xpos, fy))

    def rect(self, rx, ry, rw, rh, color = (255,255,255)):
        pygame.draw.rect(self.screen, color, (rx, ry, rw, rh))

    def line(self, point1, point2, color = (255,255,255)):
        pygame.draw.line(self.screen, color, point1, point2)

    def wtext(self, text, color, rect, font, aa=False, bkg=None):
        rect = pygame.Rect(rect)
        y = rect.top
        lineSpacing = -2
        # get the height of the font
        fontHeight = font.size("Tg")[1]
        while text:
            i = 1
            # determine if the row of text will be outside our area
            if y + fontHeight > rect.bottom:
                break
            # determine maximum width of line
            while font.size(text[:i])[0] < rect.width and i < len(text):
                i += 1
            # if we've wrapped the text, then adjust the wrap to the last word      
            if i < len(text): 
                i = text.rfind(" ", 0, i) + 1
            # render the line and blit it to the surface
            if bkg:
                image = font.render(text[:i], 1, color, bkg)
                image.set_colorkey(bkg)
            else:
                image = font.render(text[:i], aa, color)
            self.screen.blit(image, (rect.left, y))
            y += fontHeight + lineSpacing
            # remove the text we just blitted
            text = text[i:]
        return text

    def lines(self, pointlist, color=(255,255,255)):
      pygame.draw.aalines(self.screen, color, False, pointlist)

    def dispZoomImage(self, imageFile, rect):
        (x, y, bx, by) = rect
        image = pygame.image.load(imageFile)
        ix, iy = image.get_size()
        sfx = bx / ix
        sfy = by / iy
        scale_factor = max(sfx, sfy)
        sx = int(ix * scale_factor)
        sy = int(iy * scale_factor)
        resized = pygame.transform.smoothscale(image, (sx, sy))
        #resized = pygame.transform.scale(image, (sx, sy))
        crx = int((sx - bx) / 2) # centering
        cry = int((sy - by) / 2) 
        self.screen.blit(resized, (x, y), (crx, cry, bx, by))

    def displayImage(self, imageFile, rect):
        (x, y, bx, by) = rect
        image = pygame.image.load(imageFile)
        ix,iy = image.get_size()
        if ix > iy:
            # fit to width
            scale_factor = bx/float(ix)
            sy = scale_factor * iy
            if sy > by:
                scale_factor = by/float(iy)
                sx = scale_factor * ix
                sy = by
            else:
                sx = bx
        else:
            # fit to height
            scale_factor = by/float(iy)
            sx = scale_factor * ix
            if sx > bx:
                scale_factor = bx/float(ix)
                sx = bx
                sy = scale_factor * iy
            else:
                sy = by
        sx = int(sx)
        sy = int(sy)
        resized = pygame.transform.smoothscale(image, (sx, sy))
        if (sx < bx):
            ox = int((bx - sx) / 2)
        else:
            ox = 0
        if (sy < by):
            oy = int((by - sy) / 2)
        else: 
            oy = 0
        self.screen.blit(resized, (x + ox, y + oy))

    def update(self):
        pygame.display.update()
