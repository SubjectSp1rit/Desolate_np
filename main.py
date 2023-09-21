import pygame
import math
import sys
import random
# deque позволяет быстро перемещать элементы списков из начала в конец
from collections import deque

# config (настройки экрана и вывода)
block_size = 100  # размер каждой клетки на игровом поле
width = 1200
height = 800
texture_width = 1200  # ширина и высота текстуры. От этого зависит четкость текстуры
texture_height = 1200
number_of_rays = 600  # количество испускаемых лучей из позиции игрока. От этого зависит четкость игры
field_of_view = 1  # область видимости игрока
angle_between_beam = field_of_view / number_of_rays  # угол между лучами
distance = 2 * (number_of_rays / (2 * math.tan(field_of_view / 2)))  # расстояние от игрока до стены
projection_coefficient = distance * block_size  # коэффициент отображения, от него зависит "растяжение" картинки
screen_scale = width // number_of_rays  # масштабирующий коэффициент во избежание зависаний
central_ray = number_of_rays // 2 - 1

pygame.init()
pygame.display.set_caption('Desolate')
pygame.display.set_icon(pygame.image.load('pictures/icon.ico'))
screen = pygame.display.set_mode((width, height))
map_screen = pygame.Surface((width, height))  # отдельный холст для вывода на него миникарты

# карта
_ = False  # '_' - является пустым пространством, где может ходить игрок
map = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, _, _, _, _, 1, 1, _, _, _, _, _, _, _, _, _, _, 1, _, 1, 1, _, _, 1],
    [1, _, 1, 1, _, _, _, _, _, _, 1, 1, 1, _, _, 1, _, _, _, _, 1, _, _, 1],
    [1, _, 1, _, _, _, 1, _, _, _, _, 1, 1, _, _, _, 1, _, _, _, _, _, _, 1],
    [1, _, 1, 1, _, _, _, _, _, _, _, _, 1, _, 1, _, _, 1, _, _, _, _, _, 1],
    [1, _, _, _, _, _, _, _, _, 1, 1, _, 1, _, _, _, _, _, _, 1, 1, _, _, 1],
    [1, _, 1, _, _, _, 1, _, _, 1, _, _, 1, _, _, _, 1, _, _, 1, 1, 1, _, 1],
    [1, _, _, 1, _, _, 1, _, _, _, _, _, _, _, 1, _, 1, _, _, _, _, _, _, 1],
    [1, _, _, _, _, _, _, _, _, _, _, _, _, 1, 1, _, 1, _, _, _, _, _, 1, 1],
    [1, _, _, _, _, _, 1, 1, _, 1, _, _, _, 1, 1, _, _, _, 1, 1, _, _, _, 1],
    [1, _, 1, _, _, 1, _, 1, _, _, 1, _, _, _, _, _, 1, _, 1, 1, _, 1, _, 1],
    [1, _, 1, _, _, _, _, _, _, 1, _, _, 1, _, _, _, 1, _, _, _, _, 1, _, 1],
    [1, _, 1, _, _, _, 1, _, _, _, _, _, 1, 1, _, _, _, _, _, _, _, _, _, 1],
    [1, _, _, _, _, _, _, _, 1, _, _, _, _, _, _, _, 1, _, 1, _, _, _, _, 1],
    [1, _, _, 1, 1, 1, _, _, _, _, 1, _, _, _, _, _, 1, _, _, _, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

world_map = dict()  # словарь координат всех стен для отображения
mini_map = set()
collision_objects = []  # список стен, через которые нельзя пройти
for i, column in enumerate(map):  # проходимся по всей карте и собираем значения стен (для наложения текстур)
    for j, line in enumerate(column):
        if line:  # если стена не является '_' - добавляем в словарь
            mini_map.add((j * block_size // 2, i * block_size // 2))
            # добавляем стену в список коллизий
            collision_objects.append(pygame.Rect(j * block_size, i * block_size, block_size, block_size))
            if line == '_':
                continue
            elif line == 1:
                world_map[(j * block_size, i * block_size)] = 1
            elif line == 2:
                world_map[(j * block_size, i * block_size)] = 2
            elif line == 3:
                world_map[(j * block_size, i * block_size)] = 3


# первоначальная позиция игрока (центр карты)
player_position = (len(map[0]) * block_size // 2, len(map) * block_size // 2)
player_angle = 0  # направление взгляда игрока
player_speed = 3  # скорость передвижения игрока


class Rendering:
    def __init__(self, screen, keyboard, clock, textures):
        self.schet = 0
        self.screen = screen
        self.keyboard = keyboard
        self.clock = clock
        self.font = pygame.font.SysFont('Arial', 36, bold=True)  # загружаем шрифт
        self.textures = textures
        self.menu_flag = True
        self.menu_picture = pygame.image.load('pictures/background.jpg').convert()
        self.menu_picture2 = pygame.image.load('pictures/background2.jpg').convert()
        self.black_screen = pygame.image.load('pictures/black_screen.png').convert()

        # базовая картинка оружия
        self.weapon_base_sprite = pygame.image.load(f'sprites/weapons/railgun/shot/0.png').convert_alpha()
        # анимация выстрела оружия
        self.weapon_shot_animation = deque([pygame.image.load(f'sprites/weapons/railgun/shot/{i}.png').convert_alpha()
                                            for i in range(10)])
        # размер оружия
        self.weapon_rect = self.weapon_base_sprite.get_rect()
        # позиция оружия на экране
        self.weapon_position = (600 - self.weapon_rect.width // 4.3, height - self.weapon_rect.height)
        self.counter = 0
        self.shot_animation_count = 0
        self.shot_animation_trigger = True
        self.sound_shot_flag = True
        self.shot_sound = pygame.mixer.Sound('sounds/railgun_shot.wav')
        self.pre_menu_sound = pygame.mixer.Sound(f'sounds/pre_menu{random.randint(1, 2)}.wav')
        self.button_pressed_sound = pygame.mixer.Sound('sounds/button.wav')
        self.shot_sound.set_volume(0.5)
        # взрыв на стене
        self.sfx = deque([pygame.image.load(f'sprites/weapons/sfx/{i}.png').convert_alpha() for i in range(11)])
        self.sfx_counter = 0

    # отрисовка всех объектов в игре (стен и нпс)
    def objects_rendering(self, world_objects):
        # сортируем объекты по расстоянию до них, начиная с дальних
        for elem in sorted(world_objects, key=lambda x: x[0], reverse=True):
            # если объект не равен False, рисуем его
            if elem[0]:
                # достаем все значения и отрисовываем объект
                _, object, object_pos = elem
                self.screen.blit(object, object_pos)

    # отрисовка оружия игрока
    def player_weapon(self, shots):
        if self.keyboard.is_shot:
            # звук выстрела
            if self.sound_shot_flag:
                self.shot_sound.play()
                self.sound_shot_flag = False
            self.weapon_position = (600 - self.weapon_rect.width // 3.8 + 100, height - self.weapon_rect.height)
            # берем ближайший объект находящийся под огнем
            self.shot_projection = min(shots)[1] // 2
            self.bullet_sfx()
            shot_sprite = self.weapon_shot_animation[0]
            self.screen.blit(shot_sprite, self.weapon_position)
            self.shot_animation_count += 1
            if self.shot_animation_count == 3:
                self.weapon_shot_animation.rotate(-1)
                self.shot_animation_count = 0
                self.counter += 1
                self.shot_animation_trigger = False
            if self.counter == len(self.weapon_shot_animation):
                self.keyboard.is_shot = False
                self.counter = 0
                self.sfx_counter = 0
                self.shot_animation_trigger = True
        else:
            self.weapon_position = (600 - self.weapon_rect.width // 4.3 + 100, height - self.weapon_rect.height)
            self.sound_shot_flag = True
            self.screen.blit(self.weapon_base_sprite, self.weapon_position)

    # анимация взрыва на стене
    def bullet_sfx(self):
        if self.sfx_counter < len(self.sfx):
            # изменяем размер взрыва
            sfx = pygame.transform.scale(self.sfx[0], (self.shot_projection, self.shot_projection))
            # берем длину и ширину спрайта
            sfx_rect = sfx.get_rect()
            # отрисовываем спрайт
            self.screen.blit(sfx, (600 - sfx_rect.width // 2, 400 - sfx_rect.height // 2))
            self.sfx_counter += 1
            # двигаем список на единицу вправо
            self.sfx.rotate(-1)

    # отрисовка игрового меню
    def menu(self):
        # запускаем мелодию
        self.pre_menu_sound.set_volume(0.2)
        # этот цикл рисует плавное затемнение
        for i in range(150):
            self.black_screen.set_alpha(255 - i * 2)
            self.screen.blit(self.menu_picture, (0, 0))
            self.screen.blit(self.black_screen, (0, 0))
            pygame.display.flip()
            self.clock.tick(60)
            pygame.display.flip()
            if i == 1:
                self.pre_menu_sound.play()
        # этот цикл рисует плавное затемнение
        for i in range(150):
            self.black_screen.set_alpha(i * 2)
            self.screen.blit(self.menu_picture, (0, 0))
            self.screen.blit(self.black_screen, (0, 0))
            pygame.display.flip()
            self.clock.tick(60)
        self.pre_menu_sound.stop()
        # после проигрывания заставки включаем музыку в меню
        menu_music = pygame.mixer.Sound('sounds/menu_music.mp3')
        menu_music.play()
        menu_music.set_volume(0.1)
        button_font = pygame.font.Font('font/wiguru.ttf', 100)
        button_start = pygame.Rect(0, 0, 400, 150)
        button_start.center = 600, 400
        button_exit = pygame.Rect(0, 0, 400, 150)
        button_exit.center = 600, 400 + 200
        # пока пользователь находится в меню делаем след. действия:
        while self.menu_flag:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            # отрисовываем кнопки
            start = button_font.render('START', 1, pygame.Color('black'))
            exit = button_font.render('EXIT', 1, pygame.Color('black'))

            self.screen.blit(self.menu_picture2, (0, 0))

            pygame.draw.rect(self.screen, (0, 0, 0), button_start, border_radius=10, width=8)
            self.screen.blit(start, (button_start.centerx - 100, button_start.centery - 45))

            pygame.draw.rect(self.screen, (0, 0, 0), button_exit, border_radius=10, width=8)
            self.screen.blit(exit, (button_exit.centerx - 70, button_exit.centery - 45))
            # отслеживаем перемещение и нажатия мышки
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = pygame.mouse.get_pressed()
            # если игрок наводится курсором на кнопку START
            if button_start.collidepoint(mouse_pos):
                # меняем цвет
                pygame.draw.rect(self.screen, (0, 0, 0), button_start, border_radius=10)
                start = button_font.render('START', 1, pygame.Color('white'))
                self.screen.blit(start, (button_start.centerx - 100, button_start.centery - 45))
                # а в случае нажатия ЛКМ останавливаем музыку и запускаем игру
                if mouse_click[0]:
                    self.button_pressed_sound.play()
                    # этот цикл рисует плавное затемнение
                    for i in range(50):
                        self.black_screen.set_alpha(i)
                        self.screen.blit(self.black_screen, (0, 0))
                        pygame.display.flip()
                        self.clock.tick(60)
                    self.black_screen.set_alpha(255)
                    self.menu_flag = False
                    menu_music.stop()
                    spawn_music = pygame.mixer.Sound('sounds/spawn.mp3')
                    spawn_music.play()
                    spawn_music.set_volume(0.4)
                    game_music = pygame.mixer.Sound('sounds/menu_music1993.mp3')
                    game_music.play()
                    game_music.set_volume(0.1)
            # если игрок наводится курсором на кнопку EXIT
            elif button_exit.collidepoint(mouse_pos):
                # меняем цвет
                pygame.draw.rect(self.screen, (0, 0, 0), button_exit, border_radius=10)
                exit = button_font.render('EXIT', 1, pygame.Color('white'))
                self.screen.blit(exit, (button_exit.centerx - 70, button_exit.centery - 45))
                # а в случае нажатия ЛКМ выключаем игру
                if mouse_click[0]:
                    self.button_pressed_sound.play()
                    # этот цикл рисует плавное затемнение
                    for i in range(50):
                        self.black_screen.set_alpha(i)
                        self.screen.blit(self.black_screen, (0, 0))
                        pygame.display.flip()
                        self.clock.tick(60)
                    pygame.quit()
                    sys.exit()

            pygame.display.flip()
            self.clock.tick(20)


# пускает 1 луч прямо по центру экрана и определяет, видят ли объекты игрока для включения анимации
# работает по принципу уже имеющейся функции Ray Casting, так что писать подробные комментарии бессмысленно
def sprite_field_of_view(npc_x, npc_y, world_map, player_pos):
    player_x, player_y = player_pos  # положение игрока
    cell_x, cell_y = take_cords(player_x, player_y)  # клетка где находится игрок
    difference_x, difference_y = player_x - npc_x, player_y - npc_y  # разница в расстоянии между игроком и объектом
    actual_angle = math.atan2(difference_y, difference_x)
    actual_angle += math.pi
    sin_a = math.sin(actual_angle)
    cos_a = math.cos(actual_angle)
    if not sin_a:
        sin_a = 0.001
    if not cos_a:
        cos_a = 0.001
    if cos_a >= 0:
        x = cell_x + block_size
        offset_x = 1
    else:
        x = cell_x
        offset_x = -1
    for _ in range(0, int(abs(difference_x)) // block_size):
        vertical_depth = (x - player_x) / cos_a
        parallax_v = player_y + vertical_depth * sin_a
        vertical_block = take_cords(x + offset_x, parallax_v)
        if vertical_block in world_map:
            return False
        x += offset_x * block_size
    if sin_a >= 0:
        y = cell_y + block_size
        offset_y = 1
    else:
        y = cell_y
        offset_y = -1
    for _ in range(0, int(abs(difference_y)) // block_size):
        depth_h = (y - player_y) / sin_a
        parallax_h = player_x + depth_h * cos_a
        horizontal_block = take_cords(parallax_h, y + offset_y)
        if horizontal_block in world_map:
            return False
        y += offset_y * block_size
    return True


# взаимодействие клавиатуры с игрой
class KeyboardControl:
    def __init__(self, world_objects):
        self.x, self.y = player_position  # координаты игрока
        self.world_objects = world_objects  # список спрайтов на карте
        self.angle = player_angle  # направление взгляда игрока
        self.player_hit_box_size = 25  # размер hit-box'а игрока
        # размеры игрока на карте и его позиция
        self.rect = pygame.Rect(*player_position, self.player_hit_box_size, self.player_hit_box_size)
        self.is_shot = False  # False - игрок не стреляет. True - игрок стреляет.
        self.minimap_switch = False  # флаг для переключения карты
        self.fps_switch = False  # флаг для переключения FPS-счетчика


    @property
    def take_position(self):  # удобная функция для возврата позиции игрока для других классов
        return (self.x, self.y)

    @property
    def collision_list(self):  # возвращает список всех объектов, имеющих коллизию (непроходимые)
        return collision_objects + [pygame.Rect(*elem.take_position, elem.sprite_hit_box_size,
                                              elem.sprite_hit_box_size) for elem in self.world_objects if elem.blocked]

    # определение столкновения игрока с объектами, имеющими коллизию
    def detect_collision(self, next_x, next_y):
        # грубо говоря, следующая позиция игрока после нажатой кнопки, в случае, если там коллизионный объект
        # то отключаем нужную ось для ходьбы (чтобы "скользить")
        next_rect = self.rect.copy()
        # перемещаем копию нашего игрока вперед
        next_rect.move_ip(next_x, next_y)
        # это стены, с которыми столкнулся игрок на следующем шаге
        hits = next_rect.collidelistall(self.collision_list)

        # если столкнулся, то делаем след. действия:
        if len(hits):
            x_diff = 0
            y_diff = 0
            # перебираем каждое столкновение
            for hit in hits:
                # размер объекта, с которым мы столкнулись
                hit_rect = self.collision_list[hit]
                # если игрок шел по оси х:
                if next_x > 0:
                    x_diff += next_rect.right - hit_rect.left
                else:
                    x_diff += hit_rect.right - next_rect.left
                # если игрок шел по оси у:
                if next_y > 0:
                    y_diff += next_rect.bottom - hit_rect.top
                else:
                    y_diff += hit_rect.bottom - next_rect.top
            # если игрок находится в углу:
            if abs(x_diff - y_diff) < 10:
                next_x, next_y = 0, 0
            # если игрок столкнулся с горизонтальной стеной, отключаем вертикальное движение
            elif x_diff > y_diff:
                next_y = 0
            # если игрок столкнулся с вертикальной стеной, отключаем горизонтальное движение
            elif y_diff > x_diff:
                next_x = 0
        # если не столкнулся, то прибавляем шаг к позиции игрока
        self.x += next_x
        self.y += next_y

    def keyboard_buttons(self):
        keys = pygame.key.get_pressed()  # отслеживание нажатых клавиш
        if keys[pygame.K_ESCAPE]:  # при нажатии ESC игра закрывается
            saving_data()
            exit()
        if keys[pygame.K_w]:  # движение вперед
            next_x = player_speed * math.cos(self.angle)  # следующий шаг по оси х
            next_y = player_speed * math.sin(self.angle)  # следующий шаг по оси у
            self.detect_collision(next_x, next_y)  # определяет столкновение со стеной
        if keys[pygame.K_s]:  # движение назад
            next_x = -player_speed * math.cos(self.angle)  # следующий шаг по оси х
            next_y = -player_speed * math.sin(self.angle)  # следующий шаг по оси у
            self.detect_collision(next_x, next_y)  # определяет столкновение со стеной
        if keys[pygame.K_a]:  # движение влево
            next_x = player_speed * math.sin(self.angle)  # следующий шаг по оси х
            next_y = -player_speed * math.cos(self.angle)  # следующий шаг по оси у
            self.detect_collision(next_x, next_y)  # определяет столкновение со стеной
        if keys[pygame.K_d]:  # движение вправо
            next_x = -player_speed * math.sin(self.angle)  # следующий шаг по оси х
            next_y = player_speed * math.cos(self.angle)  # следующий шаг по оси у
            self.detect_collision(next_x, next_y)  # определяет столкновение со стеной
        if keys[pygame.K_LEFT]:
            self.angle -= 0.05
        if keys[pygame.K_RIGHT]:
            self.angle += 0.05
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                saving_data()
                exit()
            # если нажимаем на ЛКМ, то производится выстрел
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.is_shot is False:
                    self.is_shot = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:  # вкл/вкл карту
                    if self.minimap_switch:
                        self.minimap_switch = False
                    else:
                        self.minimap_switch = True
                if event.key == pygame.K_f:  # вкл/вкл FPS-счетчик
                    if self.fps_switch:
                        self.fps_switch = False
                    else:
                        self.fps_switch = True
        self.rect.center = self.x, self.y  # изменяем позицию "тела" игрока

    # управление мышкой
    def mouse_move(self):
        # когда курсор находится в окне игры:
        if pygame.mouse.get_focused():
            # переносим указатель в центр экрана
            pygame.mouse.set_pos((width // 2, height // 2))
            # меняем угол игрока в зависимости от разности координат
            self.angle += (pygame.mouse.get_pos()[0] - width // 2) * 0.004
        self.angle %= math.pi * 2


# взаимодействие со спрайтами
class Sprites:
    def __init__(self, settings, pos):
        self.actual_ray = central_ray
        self.creature_angry_trigger = False  # триггер анимации спрайта
        self.base = settings['base'].copy()
        self.offset = settings['offset']
        self.dead_offset = settings['dead_offset']
        self.scale = settings['scale']
        self.sprite_hit_box_size = settings['sprite_hit_box_size']
        self.peaceful_animation = settings['peaceful_animation'].copy()
        self.death_animation = settings['death_animation'].copy()
        self.angry_animation = settings['angry_animation'].copy()
        self.is_dead = settings['is_dead']
        self.blocked = settings['blocked']
        self.kind = settings['kind']
        pos_x, pos_y = pos[0], pos[1]
        self.x, self.y = pos_x * block_size, pos_y * block_size
        self.death_counter = 0  # счетчик анимаций смерти
        self.counter = 0  # счетчик анимаций, доходя до которого спрайт меняется на следующий

    # возвращает расстояние и проекцию спрайта, который находится под огнем
    @property
    def is_on_fire(self):
        if central_ray - self.sprite_hit_box_size // 2 < self.actual_ray < central_ray + self.sprite_hit_box_size // 2\
                and self.blocked:
            return self.distance_to_sprite, self.sprite_projection_height
        return float('inf'), None

    # возвращает центральную позицию спрайта
    @property
    def take_position(self):
        return self.x - self.sprite_hit_box_size // 2, self.y - self.sprite_hit_box_size // 2

    # расположение объекта
    def object_position(self, keyboard):
        # находим разницу координат между игроком и спрайтом
        sprite_x, sprite_y = self.x - keyboard.x, self.y - keyboard.y
        self.distance_to_sprite = math.sqrt(sprite_x ** 2 + sprite_y ** 2)  # расстояние до спрайта
        # радианный угол области видимости спрайта
        radian_angle = math.atan2(sprite_y, sprite_x)
        angle_diff_between_sprite_and_player = radian_angle - keyboard.angle
        if (sprite_x > 0 and 180 <= math.degrees(keyboard.angle) <= 360) or (sprite_x < 0 and sprite_y < 0):
            angle_diff_between_sprite_and_player += math.pi * 2
        # корректировка радианного угла
        radian_angle -= 1.4 * angle_diff_between_sprite_and_player
        # смещение спрайта относительно центрального луча
        offset_ray = int(angle_diff_between_sprite_and_player / angle_between_beam)
        self.actual_ray = central_ray + offset_ray  # луч, на котором находится спрайт (центральный)
        # корректируем расст. до спрайта
        self.distance_to_sprite *= math.cos(field_of_view / 2 - self.actual_ray * angle_between_beam)

        # проверка попадания луча на котором находится спрайт в наш FOV
        if 0 <= self.actual_ray + 300 <= number_of_rays -1 + 2 * 300 and self.distance_to_sprite > 30:
            # проэкц. высота спрайта
            self.sprite_projection_height = min(int(projection_coefficient / self.distance_to_sprite), 1600)
            sprite_width = int(self.sprite_projection_height * self.scale[0])  # ширина спрайта
            sprite_height = int(self.sprite_projection_height * self.scale[1])  # высота спрайта
            offset = sprite_height // 2 * self.offset  # регулируем высоту нахождения спрайта относительно игрока

            # если спрайт мертв и он не бессмертен, то выполняются след. действия:
            if self.is_dead and self.is_dead != 'immortal':
                sprite_object = self.sprite_dead_animation()  # запускаем анимацию смерти
                offset = (sprite_height // 2) * self.dead_offset  # опускаем спрайт на землю
                sprite_height = int(sprite_height / 1.3)  # уменьшаем высоту спрайта
            # если же спрайт жив, то запускаем анимацию действия
            elif self.creature_angry_trigger:
                sprite_object = self.sprite_angry_animation()
            else:
                sprite_object = self.sprite_peaceful_animation()

            # высчитываем позицию спрайта относительно его луча
            sprite_pos = (self.actual_ray * screen_scale - (sprite_width // 2), 400 - (sprite_height // 2) + offset)
            # масштабируем спрайт по размеру его проекции
            sprite = pygame.transform.scale(sprite_object, (sprite_width, sprite_height))
            return (self.distance_to_sprite, sprite, sprite_pos)
        else:
            return (False,)

    # анимация действия и передвижения объекта если он нас видит
    def sprite_move(self, world_objects, keyboard):
        for elem in world_objects:
            if elem.kind == 'creature' and not elem.is_dead:
                # если объект жив и является существом, а также видит игрока, то он начинает двигаться в сторону игрока
                if sprite_field_of_view(elem.x, elem.y, world_map, keyboard.take_position):
                    elem.creature_angry_trigger = True
                    # движение объекта в сторону игрока
                    if abs(elem.distance_to_sprite) > block_size:
                        # не важно, смотрит ли игрок на объект, объект все равно будет двигаться если видит игрока
                        # но минимальное расстояние до объекта остается 1 клетка игрового поля
                        pl_pos = keyboard.take_position
                        difference_x = elem.x - pl_pos[0]
                        difference_y = elem.y - pl_pos[1]
                        if difference_x < 0:
                            elem.x += 1
                        else:
                            elem.x -= 1
                        if difference_y < 0:
                            elem.y += 1
                        else:
                            elem.y -= 1
                    pass
                # если он не видит игрока, тогда анимации нет
                else:
                    elem.creature_angry_trigger = False
        pass

    def sprite_death(self, keyboard, drawing, world_objects, death_sound):
        if keyboard.is_shot and drawing.shot_animation_trigger:
            # ищем ближайший объект
            for elem in sorted(world_objects, key=lambda elem: elem.distance_to_sprite):
                if elem.is_on_fire[1]:
                    if not elem.is_dead:
                        # через функцию определяем находится ли объект в диапазоне поражения от выстрела
                        if sprite_field_of_view(elem.x, elem.y, world_map, keyboard.take_position):
                            # в случае, если это существо, то при смерти оно издает звук
                            if elem.kind == 'creature':
                                death_sound.play()
                            # изменяем объект на мертвый
                            elem.is_dead = True
                            # позволяем игроку проходить через ранее непроходимый объект
                            elem.blocked = None
                            drawing.shot_animation_trigger = False
                    break

    # анимация спрайта без необходимости видеть игрока
    def sprite_peaceful_animation(self):
        if self.peaceful_animation and self.distance_to_sprite <= 800:
            # меняем спрайт на первый спрайт анимации
            sprite_object = self.peaceful_animation[0]
            if self.counter < 10:
                self.counter += 1
            else:
                # двигаем каждый элемент списка вперед
                self.peaceful_animation.rotate()
                # обнуляем счетчик
                self.counter = 0
            return sprite_object
        return self.base

    # анимация спрайта в случае если он вас видит
    def sprite_angry_animation(self):
        sprite_object = self.angry_animation[0]
        if self.counter < 10:
            self.counter += 1
        else:
            self.angry_animation.rotate()
            self.counter = 0
        return sprite_object

    # анимация смерти спрайта
    def sprite_dead_animation(self):
        if len(self.death_animation):
            self.dead_sprite = self.death_animation[0]
            if self.death_counter < 10:
                self.death_counter += 1
            else:
                self.dead_sprite = self.death_animation.popleft()
                self.death_counter = 0
        return self.dead_sprite


# возвращает верхний левый угол квадрата, в котором находится игрок
def take_cords(a, b):
    return (a // block_size) * block_size, (b // block_size) * block_size


# отрисовка стен и текстур
def ray_casting(keyboard, textures):
    # эта часть кода нужна для вычисления данных об отрисовке стен, непосредственно сам ray casting
    player_pos = keyboard.take_position  # координаты игрока
    player_angle = keyboard.angle  # текущий угол игрока
    texture_vertical, texture_horizontal = 1, 1  # номер текстуры для горизонтальных и вертикальных стен
    x_start, y_start = player_pos  # начальная координата лучей
    # координата верхнего левого угла квадрата, в котором находится игрок в данный момент
    x_cell, y_cell = take_cords(x_start,
                             y_start)
    actual_angle = player_angle - field_of_view / 2  # первый луч (FOV * 2 - последний луч)
    completed_walls = []  # список уже готовых стен
    for _ in range(number_of_rays):  # проходимся по каждому лучу
        sin_a, cos_a = math.sin(actual_angle), math.cos(actual_angle)
        if not sin_a:
            sin_a = 0.001
        if not cos_a:
            cos_a = 0.001
        # вертикальные стены
        if cos_a >= 0:  # в зависимости от значения cos определим значение x - текущее положение,
            x = x_cell + block_size  # а dx - вспом. перем, при помощи которой получаем очередную вертикаль
            offset_x = 1
        else:
            x = x_cell
            offset_x = -1
        for _ in range(0, len(map[0]) * block_size, block_size):  # проходимся по каждой клетке карты
            vertical_depth = (x - x_start) / cos_a  # расстояние до вертикали
            vertical_y_cord = y_start + vertical_depth * sin_a  # координата у этой вертикали
            vertical_block = take_cords(x + offset_x, vertical_y_cord)
            if vertical_block in world_map:
                texture_vertical = world_map[vertical_block]  # определяем номер текстуры
                break
            x += offset_x * block_size  # если пересечения нет - переходим к следующей вертикали
        # горизонтальные стены
        if sin_a >= 0:  # в зависимости от значения sin определим значение у = текущее положение,
            y = y_cell + block_size  # а dy - вспом. перем, при помощи которой получаем очередную горизонталь
            offset_y = 1
        else:
            y = y_cell
            offset_y = -1
        for _ in range(0, len(map) * block_size, block_size):  # проходимся по каждой клетке карты
            horizontal_depth = (y - y_start) / sin_a  # расстояние до горизонтали
            horizontal_x_cord = x_start + horizontal_depth * cos_a  # координата х этой горизонтали
            horizontal_block = take_cords(horizontal_x_cord, y + offset_y)
            if horizontal_block in world_map:
                texture_horizontal = world_map[horizontal_block]  # определяем номер текстуры
                break
            y += offset_y * block_size  # если пересечения нет - переходим к следующей горизонтали
        if vertical_depth < horizontal_depth:
            depth, offset, texture = vertical_depth, vertical_y_cord, texture_vertical
        else:
            depth, offset, texture = horizontal_depth, horizontal_x_cord, texture_horizontal
        parallax = int(offset) % block_size  # вычисление смещения текстуры
        depth *= math.cos(player_angle - actual_angle)  # убираем "эффект рыбьего глаза"
        depth = max(depth, 0.00001) # избегаем деления на 0
        projection_height = int(projection_coefficient / depth)  # сота проекции стены

        completed_walls.append(
            (depth, parallax, projection_height, texture))  # добавление стены в список для отрисовки объектов
        actual_angle += angle_between_beam  # переходим к следующему лучу

    # эта часть кода уже непосредственно накладывает текстуры на полученные данные о стенах
    # размер проекции взрыва на центральном луче
    wall_shot = completed_walls[central_ray][0], completed_walls[central_ray][2]
    walls = []
    for i, elem in enumerate(completed_walls):
        depth, parallax, projection_height, texture = elem
        # когда мы подходим к стене слишком близко и она становится больше высоты экрана, падает фпс, поэтому:
        if projection_height > height:
            # берем только часть от проекции текстуры, которая будет во столько же раз меньше
            # во сколько проекция больше экрана
            coefficient = projection_height / height
            texture_height_without_fish_eye = texture_height / coefficient
            # подповерхность текстуры для отрисовки
            wall = textures[texture].subsurface(parallax * texture_width // block_size,
                                                texture_height // 2 - texture_height_without_fish_eye // 2,
                                                texture_width // block_size, texture_height_without_fish_eye)
            wall = pygame.transform.scale(wall, (screen_scale, height))
            wall_position = (i * screen_scale, 0)
        else:
            wall = textures[texture].subsurface(parallax * texture_width // block_size, 0,
                                                texture_width // block_size, 1200)
            wall = pygame.transform.scale(wall, (screen_scale, projection_height))
            wall_position = (i * screen_scale, 400 - projection_height // 2)
        walls.append((depth, wall, wall_position))
    return walls, wall_shot


# сохранение данных в текстовый документ
def saving_data():
    pass
    # with open('game_data.txt') as f1:
    #     data = f1.readlines()
    # coins = int(data[0].split('=')[1])
    # count_of_killed_monsters = int(data[1].split('=')[1])
    # with open('game_data.txt', 'w') as f2:
    #     coins += session_coins
    #     count_of_killed_monsters += session_monsters
    #     f2.write('coins:', coins )
    #     f2.write('total_killed_monsters', count_of_killed_monsters)


# отрисовка фона игры (пол и потолок)
def background(angle):
    # небо
    degree = math.degrees(angle)
    sky_parallax = -10 * degree % width  # смещение неба
    sky_texture = pygame.image.load('pictures/space.jpg').convert()  # текстура неба
    screen.blit(sky_texture, (sky_parallax, 0))
    screen.blit(sky_texture, (sky_parallax - width, 0))
    screen.blit(sky_texture, (sky_parallax + width, 0))
    # пол
    pygame.draw.rect(screen, (60, 60, 60), (0, 400, width, 400))


# отрисовка карты
def minimap():
    map_screen.fill((0, 0, 0))  # закрашиваем полотно в черный цвет
    pygame.draw.circle(map_screen, (255, 0, 0), (int(keyboard.x // 2), int(keyboard.y // 2)), 4)  # рисуем игрока
    for i, j in mini_map:  # проходимся по клеткам карты
        pygame.draw.rect(map_screen, (0, 180, 250), (i, j, block_size // 2, block_size // 2), 2)  # отрисовываем стены
    map_screen.set_alpha(150)  # определяем прозрачность карты
    screen.blit(map_screen, (0, 0))  # выводим карту на экран


# отрисовка FPS-счетчика
def fps():
    fps_count = str(int(clock.get_fps()))  # считываем кол-во FPS
    render = pygame.font.SysFont('Arial', 30, bold=True).render(fps_count, 0, (0, 180, 250))  # отрисовываем FPS
    screen.blit(render, (10, 5))  # выводим счетчик на экран


# проверка победы
def victory_check(world_objects):
    # если все существа мертвы, запускаем анимацию победы
    if not len([x for x in world_objects if x.kind == 'creature' and not x.is_dead]):
        pygame.mixer.stop()
        pygame.mixer.music.load('sounds/menu_music.mp3')
        pygame.mixer.music.play()
        pygame.mixer.music.set_volume(0.2)
        win_picture = pygame.image.load('pictures/win.png')
        flag = True
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    exit()
            if flag:
                for i in range(50):
                    win_picture.set_alpha(i)
                    screen.blit(win_picture, (0,0))
                    pygame.display.flip()
                    clock.tick(60)
                flag = False
            win_picture.set_alpha(255)
            screen.blit(win_picture, (0, 0))


sprites_settings = {
            'doom_cacodemon': {
                'base': pygame.image.load(f'sprites/devil/base/0.png').convert_alpha(),  # базовый спрайт
                'offset': 0.0,  # сдвиг по высоте
                'dead_offset': 0.6,  # сдвиг по высоте после смерти
                'scale': (1, 1),  # масштаб спрайта
                'sprite_hit_box_size': 50,  # размер hit-box'a спрайта
                'peaceful_animation': [],  # анимация действия (не требует взгляда игрока)
                'death_animation': deque([pygame.image.load(f'sprites/devil/death/{i}.png').convert_alpha()
                                          for i in range(6)]),  # анимация после смерти
                'angry_animation': deque([pygame.image.load(f'sprites/devil/animation/{i}.png').convert_alpha()
                                          for i in range(9)]),  # анимация действия объекта (если спрайт видит игрока)
                'is_dead': None,  # жив/мертв объект
                'blocked': True,  # имеет ли объект коллизию
                'kind': 'creature'},  # является ли спрайт монстром или декорацией

            'pop_cat': {
                'base': pygame.image.load('sprites/pop_cat/base/0.png').convert_alpha(),
                'offset': 0.66,
                'dead_offset': None,
                'scale': (0.6, 0.6),
                'sprite_hit_box_size': 50,
                'peaceful_animation': deque([pygame.image.load(f'sprites/pop_cat/animation/{i}.png').convert_alpha() for i in range(2)]),
                'death_animation': [],
                'angry_animation': [],
                'is_dead': 'immortal',
                'blocked': True,
                'kind': 'other'
            }
        }

world_objects = [
            Sprites(sprites_settings['doom_cacodemon'], (7, 4)),
            Sprites(sprites_settings['doom_cacodemon'], (2, 2)),
            Sprites(sprites_settings['doom_cacodemon'], (7, 7)),
            Sprites(sprites_settings['pop_cat'], (12, 10))
        ]

textures = {1: pygame.image.load('pictures/stone_wall.jpg').convert(),
            }


def sprite_shot(world_objects):
    return min([obj.is_on_fire for obj in world_objects], default=(float('inf'), 0))


death_sound = pygame.mixer.Sound('sounds/cacodemon_death_sound.mp3')
death_sound.set_volume(0.3)
clock = pygame.time.Clock()
keyboard = KeyboardControl(world_objects)
render = Rendering(screen, keyboard, clock, textures)

render.menu()  # запуск меню
pygame.mouse.set_visible(False)  # выключаем курсор

# монеты и кол-во убитых монстров за текущую игровую сессию (В разработке)
session_coins = 0
session_monsters = 0

running = True  # запуск игры
while running:
    # функция для считывания нажатия клавиш/выхода из игры, заменяет "for event in pygame ..."
    keyboard.keyboard_buttons()
    # функция для отслеживания изменения положения мышки
    keyboard.mouse_move()
    # отрисовка неба и пола
    background(keyboard.angle)
    # отрисовка стен и взрыва от выстрела
    ray_casting_objects = ray_casting(keyboard, textures)
    render.objects_rendering(ray_casting_objects[0] + [elem.object_position(keyboard) for elem in world_objects])
    render.player_weapon([ray_casting_objects[1], sprite_shot(world_objects)])

    if keyboard.minimap_switch:  # кнопка вкл/выкл карты
        minimap()
    if keyboard.fps_switch:  # кнопка вкл/выкл счетчика FPS
        fps()
    # проверка попадания по спрайту после выстрела
    Sprites.sprite_death('self', keyboard, render, world_objects, death_sound)
    # передвижение спрайтов
    Sprites.sprite_move('self', world_objects, keyboard)
    # в конце каждой итерации проверяем, победил ли игрок
    victory_check(world_objects)
    pygame.display.flip()  # обновление экрана
    clock.tick(60)  # не рекомендую поднимать FPS выше. Игра рассчитана именно на 60 кадров в секунду
