import random

from machine import Pin
from neopixel import NeoPixel
from time import ticks_ms, ticks_diff


class Garland(NeoPixel):

    def __init__(self, pin, num_of_leds, brightness=0.05):
        pin = Pin(pin, Pin.OUT)
        super().__init__(pin, num_of_leds)
        self.brightness = brightness
        self.timer = ticks_ms()

    def set_brightness(self, color):
        return [int(c * self.brightness) for c in color]

    def turn_on_colors(self, colours_tuple):
        for idx in range(len(colours_tuple)):
            self[idx] = self.set_brightness(colours_tuple[idx])
        self.write()

    def color_effects(self, color_effect_iter, circle_time=10):
        delta_time = circle_time * 1000 / color_effect_iter.count_of_iter_cycle
        current_time = ticks_ms()
        if current_time - self.timer > delta_time:
            self.timer = current_time
            colours_tuple = next(color_effect_iter)
            self.turn_on_colors(colours_tuple)


class ColorEffectsABC:

    def __init__(self, garland, count_of_iter_cycle):
        self.count_of_iter_cycle = count_of_iter_cycle
        self.garland = garland

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError("В потомке не реализован метод '__next__'")


class Rainbow:

    def __init__(self, count_of_iter_cycle=360):
        self.count_of_iter_cycle = count_of_iter_cycle
        self.c60 = self.count_of_iter_cycle / 6
        self.c120 = self.count_of_iter_cycle / 3
        self.c180 = self.count_of_iter_cycle / 2
        self.c240 = self.count_of_iter_cycle / 3 * 2
        self.c360 = self.count_of_iter_cycle

    def rgb_wheel(self, degree):
        def color_pattern(degree):
            degree %= self.count_of_iter_cycle
            if 0 <= degree < self.c60:
                value = degree / self.c60
            elif self.c180 <= degree < self.c240:
                value = 1 - (degree - self.c180) / self.c60
            else:
                value = 1 if self.c60 <= degree < self.c180 else 0
            return int(value * 255)

        red = color_pattern(degree - self.c240)
        green = color_pattern(degree)
        blue = color_pattern(degree - self.c120)
        return red, green, blue


class VerticalRainbow(ColorEffectsABC):

    def __init__(self, garland, start_degree=0, count_of_iter_cycle=360):
        super().__init__(garland=garland, count_of_iter_cycle=count_of_iter_cycle - 1)
        self.rainbow = Rainbow(count_of_iter_cycle=count_of_iter_cycle)
        self.degree = start_degree % count_of_iter_cycle

    def __next__(self):
        color= self.rainbow.rgb_wheel(self.degree)
        colors_tuple = [color] * len(self.garland)
        self.degree += 1
        return colors_tuple

class HorizontalRainbow(ColorEffectsABC):

    def __init__(self, garland, start_degree=0, rainbow_count=1, rainbow_speed=5, count_of_iter_cycle=360):
        super().__init__(garland=garland, count_of_iter_cycle=count_of_iter_cycle - 1)
        self.rainbow = Rainbow(count_of_iter_cycle=count_of_iter_cycle)
        self.color_shift = round(self.count_of_iter_cycle / len(garland) * rainbow_count)
        self.rainbow_speed = rainbow_speed
        self.degree = start_degree % count_of_iter_cycle

    def __next__(self):
        colors_tuple = []
        for idx in range(len(self.garland)):
            color = self.rainbow.rgb_wheel((self.degree + idx * self.color_shift) % self.count_of_iter_cycle)
            colors_tuple.append(color)
        self.degree = (self.degree + self.rainbow_speed) % self.count_of_iter_cycle
        return colors_tuple


class RandomColorCE(ColorEffectsABC):
    base_colors = [(255, 0, 0),
                   (0, 255, 0),
                   (0, 0, 255),
                   (255, 0, 255),
                   (255, 255, 0),
                   (0, 255, 255),
                   (255, 128, 0),
                   (255, 255, 255),
                   (0, 0, 0),
                   ]

    def __init__(self, garland, count_of_iter_cycle=10):
        super().__init__(garland=garland, count_of_iter_cycle=count_of_iter_cycle - 1)

    def __next__(self):
        colors_tuple = []
        for idx in range(len(self.garland)):
            red = random.randint(0, 255)
            green = random.randint(0, 255)
            blue = random.randint(0, 255)
            colors_tuple.append([red, green, blue])
        return colors_tuple


class RandomFireCE(RandomColorCE):

    def __next__(self):
        colors_tuple = []
        for idx in range(len(self.garland)):
            red = random.randint(150, 255)
            green = random.randint(0, 100)
            blue = random.randint(0, 10)
            colors_tuple.append([red, green, blue])
        return colors_tuple

class RandomBaseColorCE(RandomColorCE):

    def __next__(self):
        colors_tuple = []
        for idx in range(len(self.garland)):
            colors_tuple.append(random.choice(self.base_colors))
        return colors_tuple


class Button:
    def __init__(self, pin_number, debounce_time=50, triple_click_time=500, hold_time=1000):
        """
        Инициализация кнопки.

        :param pin_number: Номер пина, к которому подключена кнопка.
        :param debounce_time: Время антидребезга в миллисекундах (по умолчанию 50 мс).
        :param double_click_time: Время для определения двойного нажатия в миллисекундах (по умолчанию 300 мс).
        :param triple_click_time: Время для определения тройного нажатия в миллисекундах (по умолчанию 500 мс).
        :param hold_time: Время удержания кнопки для определения удержания в миллисекундах (по умолчанию 1000 мс).
        """
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self.debounce_time = debounce_time
        self.triple_click_time = triple_click_time
        self.hold_time = hold_time
        self.last_state = self.pin.value()
        self.last_change_time = ticks_ms()
        self.click_count = 0
        self.last_click_time = 0
        self.is_holding = False
        self.hold_start_time = 0

    def check_button_state(self):
        """
        Проверяет текущее состояние кнопки и обновляет внутренние переменные.
        """
        current_time = ticks_ms()
        current_state = self.pin.value()

        if current_state != self.last_state:
            if ticks_diff(current_time, self.last_change_time) > self.debounce_time:
                self.last_state = current_state
                self.last_change_time = current_time

                if not current_state:  # Кнопка нажата (состояние LOW)
                    if not self.is_holding:
                        self.hold_start_time = current_time
                    self.click_count += 1
                    self.last_click_time = current_time
                else:  # Кнопка отпущена (состояние HIGH)
                    if self.is_holding:
                        self.is_holding = False
                        return "release"
        return None

    def check_hold(self):
        """
        Проверяет, удерживается ли кнопка.

        :return: Строка "hold", если кнопка удерживается, иначе None.
        """
        current_time = ticks_ms()

        if not self.pin.value() and not self.is_holding:
            if ticks_diff(current_time, self.hold_start_time) > self.hold_time:
                self.is_holding = True
                self.click_count = 0
                return "hold"
        return None

    def check_clicks(self):
        """
        Проверяет количество нажатий и определяет одиночное, двойное, тройное нажатие или удержание кнопки.
        :return: Строка, описывающая тип нажатия.
        """
        action = self.check_button_state()
        if action:
            return action
        action = self.check_hold()
        if action:
            return action
        current_time = ticks_ms()
        if self.pin.value() and self.click_count > 0:
            if ticks_diff(current_time, self.last_click_time) > self.triple_click_time:
                if self.click_count == 1:
                    self.click_count = 0
                    return "single"
                elif self.click_count == 2:
                    self.click_count = 0
                    return "double"
                elif self.click_count == 3:
                    self.click_count = 0
                    return "triple"
                else:
                    res = f"multiple - {self.click_count}"
                    self.click_count = 0
                    return res
        return None


garland = Garland(15, 300)
button = Button(16)


vert_rainbow = VerticalRainbow(garland=garland, count_of_iter_cycle=360)
hor_rainbow = HorizontalRainbow(garland=garland, rainbow_speed=10)
hor_rainbow_10 = HorizontalRainbow(garland=garland, rainbow_count=10, rainbow_speed=10)
hor_rainbow_30 = HorizontalRainbow(garland=garland, rainbow_count=30, rainbow_speed=10)
rc_ce = RandomColorCE(garland=garland)
rbc_ce = RandomBaseColorCE(garland=garland)
r_fire_ce = RandomFireCE(garland=garland)

color_effects = [vert_rainbow, hor_rainbow, hor_rainbow_10, hor_rainbow_30, rbc_ce, r_fire_ce]

timer = ticks_ms()
idx = 0

current_eff = color_effects[random.randint(0, len(color_effects)-1)]

DELTA_TIME = 10
while True:
    action = button.check_clicks()
    if action:
        if action == "single":
            idx = (idx + 1) % len(color_effects)
            current_eff = color_effects[idx]
            timer = ticks_ms()
        if action == "double":
            idx = (idx - 1) % len(color_effects)
            current_eff = color_effects[idx]
            timer = ticks_ms()
        if action == "triple":
            while True:
                r_idx = random.randint(0, len(color_effects) - 1)
                random_effect = color_effects[r_idx]
                if random_effect != color_effects:
                    break
            current_eff = random_effect
            idx = r_idx
            timer = ticks_ms()

    if (ticks_ms() - timer) > DELTA_TIME * 1000:
        while True:
            r_idx = random.randint(0, len(color_effects)-1)
            random_effect = color_effects[r_idx]
            if random_effect != color_effects:
                break
        current_eff = random_effect
        idx = r_idx
        timer = ticks_ms()
    garland.color_effects(color_effect_iter=current_eff)
