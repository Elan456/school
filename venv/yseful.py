import math as m
import pygame

def basicinput(event,keystates):
    kright,kleft,kup,kdown,lshift = keystates
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_a:
            kleft = 1
        if event.key == pygame.K_d:
            kright = 1
        if event.key == pygame.K_w:
            kup = 1
        if event.key == pygame.K_s:
            kdown = 1
        if event.key == pygame.K_LSHIFT:
            lshift = 1
    if event.type == pygame.KEYUP:
        if event.key == pygame.K_a:
            kleft = 0
        if event.key == pygame.K_d:
            kright = 0
        if event.key == pygame.K_w:
            kup = 0
        if event.key == pygame.K_s:
            kdown = 0
        if event.key == pygame.K_LSHIFT:
            lshift = 0
    return([kright,kleft,kup,kdown,lshift])


def sigmoid(x):
    x=x/10
    y = round(1/(1+2**(-1*x)),5)

    return(y)

def cprint(a):
    for v in a:
        print(v)
def arsort(l):
    return(l[0])

def cdistance(x1,y1,x2,y2):
    d = m.sqrt((x1-x2)**2+(y1-y2)**2)
    return(d)

def bounce(v,normal,sc):
    outgoing = 2 * normal - m.pi - v[1]
    a = outgoing
    b = v[0] / sc
    return([b,a])

def veladd(v1,v2):
    tx = 0
    ty = 0

    tx += v1[0] * m.cos(v1[1])
    ty += v1[0] * m.sin(v1[1])
    tx += v2[0] * m.cos(v2[1])
    ty += v2[0] * m.sin(v2[1])

    newdir = m.atan2(ty, tx)
    newvel = m.sqrt((tx) ** 2 + (ty) ** 2)
    return([newvel,newdir])

