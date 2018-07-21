import os
import pygame
import sys

from pygame.locals import *

import config
import objects


class State:

    def handle(self, event):
        if event.type == QUIT:
            sys.exit()
        if event.type == KEYDOWN and event.type == K_ESCAPE:
            sys.exit()

    def first_display(self, screen):
        screen.fill(config.background_color)
        pygame.display.flip()

    def display(self, screen):
        pass


class Level(State):

    def __init__(self, number=1):
        self.number = number
        self.remaining = config.weights_per_level
        speed = config.drop_speed
        speed += (self.number - 1) * config.speed_increase
        self.weight = objects.Weight(speed)
        self.banana = objects.Banana()
        both = self.weight, self.banana
        self.sprites = pygame.sprite.RenderUpdates(both)

    def update(self, game):
        self.sprites.update()
        if self.banana.touches(self.weight):
            game.next_state = GameOver()
        elif self.weight.landed:
            self.weight.reset()
            self.remaining -= 1
            if self.remaining == 0:
                game.next_state = LevelCleared(self.number)

    def display(self, screen):
        screen.fill(config.background_color)
        updates = self.sprites.draw(screen)
        pygame.display.update(updates)


class Paused(State):

    finished = 0
    image = None
    text = ''

    def handle(self, event):
        State.handle(self, event)
        if event.type in [MOUSEBUTTONDOWN, KEYDOWN]:
            self.finished = 1

    def update(self, game):
        if self.finished:
            game.next_state = self.next_state()

    def first_display(self, screen):
        screen.fill(config.background_color)
        font = pygame.font.Font(None, config.font_size)
        lines = self.text.strip().splitlines()
        height = len(lines) * font.get_linesize()

        center, top = screen.get_rect().center
        top -= height // 2

        if self.image:
            image = pygame.image.load(self.image).convert()
            r = image.get_rect()
            top += r.height
            r.midbottom = center, top - 20
            screen.blit(image, r)

        antialias = 1
        black = 0, 0, 0

        for line in lines:
            text = font.render(line.strip(), antialias, black)
            r = text.get_rect()
            r.midtop = center, top
            screen.blit(text, r)
            top += font.get_linesize()

        pygame.display.flip()


class Info(Paused):
    next_state = Level
    text = '''
    In this game you are a banana,
    trying to survive a course in
    self-defense against fruit, where the
    participants will "defend" themselves
    against you with a 16 tom weight
    '''


class StartUp(Paused):
    next_state = Info
    image = config.splash_image
    text = '''
    Welcome to Squish,
    the game of Fruit Self-Defence
    '''


class LevelCleared(Paused):

    def __init__(self, number):
        self.number = number
        self.text = '''
        Level {} cleared, Click to start next level
        '''.format(self.number)

    def next_state(self):
        return Level(self.number + 1)


class GameOver(Paused):

    next_state = Level
    text = '''
    Game Over
    Click to Restart. Esc to Quit
    '''


class Game:

    def __init__(self, *args):
        path = os.path.abspath(args[0])
        dir = os.path.split(path)[0]
        os.chdir(dir)
        self.state = None
        self.next_state = StartUp()

    def run(self):
        pygame.init()
        flag = 0
        if config.full_screen:
            flag = FULLSCREEN
        screen_size = config.screen_size
        screen = pygame.display.set_mode(screen_size, flag)

        pygame.display.set_caption('Fruit Self Defence')
        pygame.mouse.set_visible(False)

        while True:
            if self.state != self.next_state:
                self.state = self.next_state
                self.state.first_display(screen)
            for event in pygame.event.get():
                self.state.handle(event)

            self.state.update(self)
            self.state.display(screen)


if __name__ == '__main__':
    game = Game(*sys.argv)
    game.run()
