import pygame
import random
import math
import time
import os

import pygame.gfxdraw

# 초기화
pygame.init()
pygame.mixer.init()


base_path = os.path.dirname(__file__)

# 배경 음악 로드 및 재생
pygame.mixer.music.load(os.path.join(base_path, "resources","background.mp3"))
pygame.mixer.music.play(-1)

# 효과음 로드
radar_sound = pygame.mixer.Sound(os.path.join(base_path, "resources","rader (2).mp3"))
detected_sound = pygame.mixer.Sound(os.path.join(base_path, "resources","Detected (2).mp3"))
lwalk_sound = pygame.mixer.Sound(os.path.join(base_path, "resources","Lwalk.mp3"))
rwalk_sound = pygame.mixer.Sound(os.path.join(base_path, "resources","Rwalk.mp3"))
running_sound = pygame.mixer.Sound(os.path.join(base_path, "resources","running (1).mp3"))
breath_control_sound = pygame.mixer.Sound(os.path.join(base_path, "resources","heart.mp3"))
blackhole_sound = pygame.mixer.Sound(os.path.join(base_path, "resources","커비 흡입-시작.mp3"))
blackhole_sound2 = pygame.mixer.Sound(os.path.join(base_path,"resources", "커비 흡입-중간.mp3"))

# 색상 정의
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0,0,255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
LIGHT_BLUE = (173, 216, 230)
ALERT_RED = (255, 100, 100)  

# 화면 크기
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Radar game")

# 레이더 반경
RADAR_RADIUS = 250
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# 레이더 회전 관련 변수
radar_angle = 0
rotation_speed = 360 / 3000 #레이더 회전 3초에 1번

# 맵 크기
MAP_SIZE = 2000

# 플레이어 설정
PLAYER_RADIUS = 10
player_x = MAP_SIZE // 2
player_y = MAP_SIZE // 2
player_speed = 2

# 플레이어 상태
player_moving = False
breath_gauge = 100
breath_recovery_rate = 0.1
breath_depletion_rate = 0.2
breath_low_threshold = 20

# 플레이어 상태 변수
can_recover_breath = True # 스테미나 회복 페널티 설정
slow_speed_timer = 0 # 속도 페널티 설정
breath_timer = 0 

acceleration = 0.2 # 가속도
deceleration = 0.1  # 감속 속도
max_speed = 5  # 최대 속도 설정
current_speed = 0  # 현재 속도

# 우주선 위치 설정
spaceship_x = random.randint(0, MAP_SIZE)
spaceship_y = random.randint(0, MAP_SIZE)

# 적 및 아이템 개수
NUM_ENEMIES = 10
NUM_ITEMS = 5

# 아이템 카운트
items_collected = 0

# 적의 타이머와 알파값을 관리할 딕셔너리
enemy_visibility = {}
detected_enemies = []

# 블랙홀 적 용도
NUM_blueENEMIES = 5
blueenemy_visibility = {}
detected_blueenemies = []
blackhole = {}

# chasing 배열 초기화
chasing = {}


# 레이더 배터리 설정
battery_percentage = 100
battery_depletion_rate = 1  # 초당 배터리 소모율

# 게임 오버 상태
game_over = False
death_alert_enemy = None  # 어떤 적에게 먹혔는지 저장

# 효과음 재생 상태 변수
radar_played = False
playing = False

# 효과음 재생 시간 및 텀 설정
walk_sound_timer = 0
walk_sound_interval = 0.5  # 걷기 소리 간격 (초)
run_sound_interval = 0.25   # 달리기 소리 간격 (초)
heart_sound_timer = -100 # 심장소리를 위한 값
heart_sound_interval = 1.85



# 걷기 소리 함수
def walksound(is_running):
    global walk_sound_timer
    current_time2 = time.time()

    if is_running:
        if current_time2 - walk_sound_timer >= run_sound_interval:
            rwalk_sound.play()
            walk_sound_timer = current_time2  # 타이머 리셋
    else:
        if current_time2 - walk_sound_timer >= walk_sound_interval:
            lwalk_sound.play()
            walk_sound_timer = current_time2  # 타이머 리셋

# 적 생성
for _ in range(NUM_ENEMIES):
    while True:
        x = random.randint(0, MAP_SIZE)
        y = random.randint(0, MAP_SIZE)
    
        # 플레이어와의 거리 계산
        distance_to_player = math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2)
        
        # 플레이어로부터 200픽셀 이상 떨어진 경우에만 적 위치 설정 (초기 돌연사 방지)
        if distance_to_player >= 200:
            enemy_visibility[(x, y)] = {
                'timer': None, 
                'alpha': 0, 
                'direction': random.uniform(0, 360), 
                'speed': 1
            }
            chasing[(x, y)] = 0
            break

# 블랙홀 적 생성
for _ in range(NUM_blueENEMIES):
    while True:
        x = random.randint(0, MAP_SIZE)
        y = random.randint(0, MAP_SIZE)
        
        # 플레이어와의 거리 계산
        distance_to_player = math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2)
            
            # 플레이어로부터 200픽셀 이상 떨어진 경우에만 적 위치 설정 (초기 돌연사 방지)
        if distance_to_player >= 200:
            blueenemy_visibility[(x, y)] = {
                'timer': None, 
                'alpha': 0, 
                'direction': random.uniform(0, 360), 
                'speed': 1,
                'is_blackhole' : False
            }
            blackhole[(x, y)] = 0
            break


# 아이템 생성
items = [(random.randint(0, MAP_SIZE), random.randint(0, MAP_SIZE)) for _ in range(NUM_ITEMS)]

# 게임 루프
running = True
breath_control = False
clock = pygame.time.Clock()



while running:
    screen.fill(BLACK)

    current_time = pygame.time.get_ticks() / 1000  # 현재 시간 계산용

    # 게임 오버 체크
    if game_over:
        font = pygame.font.SysFont(None, 55)
        text_surface = font.render("Game Over!", True, WHITE)
        screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, SCREEN_HEIGHT // 2 - text_surface.get_height() // 2))
        pygame.display.flip()
        
        # 게임 오버 상태에서 대기
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
        continue  # 게임 오버 상태에서도 루프를 계속 돌림 (오류 방지)

    # 우주선 표시
    screen_x = CENTER_X + (spaceship_x - player_x + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
    screen_y = CENTER_Y + (spaceship_y - player_y + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
    pygame.draw.rect(screen, WHITE, (screen_x - 15, screen_y - 15, 30, 30))  # 우주선을 사각형으로 표시

    # 레이더 원 그리기 [anti-aliasing]
    pygame.gfxdraw.aacircle(screen, CENTER_X, CENTER_Y, RADAR_RADIUS, GREEN) 

    # 레이더 내부의 동심원 그리기 [anti-aliasing]
    for r in range(50, RADAR_RADIUS, 50):
        pygame.gfxdraw.aacircle(screen, CENTER_X, CENTER_Y, r, GREEN)

    # 레이더 선 그리기 [Trigonometric Function 각도를 기준으로 좌표 계산]
    radar_x = CENTER_X + RADAR_RADIUS * math.cos(math.radians(radar_angle))
    radar_y = CENTER_Y + RADAR_RADIUS * math.sin(math.radians(radar_angle))
    if(battery_percentage >0):
        pygame.draw.line(screen, GREEN, (CENTER_X, CENTER_Y), (radar_x, radar_y), 2)

    # 레이더 회전
    radar_angle = (radar_angle + rotation_speed * clock.get_time()) % 360

    
    # 12시 방향의 각도 범위 설정
    if (260 <= radar_angle <= 270) and battery_percentage > 0 :  # 12시 방향 근처 and 배터리가 있을때 레이더 소리
        radar_sound.play()  # 효과음 재생


    # 적 이동 및 레이더 감지
    for enemy_pos in list(enemy_visibility.keys()):
        enemy_data = enemy_visibility[enemy_pos]
    
        # 적과 플레이어 사이의 상대 위치 계산
        relative_x = (enemy_pos[0] - player_x + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        relative_y = (enemy_pos[1] - player_y + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2

        # 거리 계산
        distance_to_player = math.sqrt(relative_x**2 + relative_y**2)

        # 각도 계산
        angle_to_player = math.degrees(math.atan2(relative_y, relative_x)) % 360

        # 적이 플레이어의 100픽셀 반경 안에 들어왔는지 체크, 숨 참고 있다면 지나치고 아니면 쫒아가는 상태
        if distance_to_player < 100 and not breath_control:
            chasing[enemy_pos] = 1
            enemy_data['speed'] = 3
        else:
            chasing[enemy_pos] = 0
            enemy_data['speed'] = 1

        # 적의 목표 위치 계산 [극좌표계]
        predicted_player_x = player_x + player_speed * math.cos(math.radians(player_x))
        predicted_player_y = player_y + player_speed * math.sin(math.radians(player_y))
        
        # 새로운 상대 위치 계산
        relative_x = (predicted_player_x - enemy_pos[0] + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        relative_y = (predicted_player_y - enemy_pos[1] + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2

        # 거리 계산
        distance_to_predicted_player = math.sqrt(relative_x**2 + relative_y**2)

        # 적이 플레이어 쫒아가게함
        if chasing[enemy_pos] == 1:
            detected_sound.play()
            enemy_data['direction'] = math.degrees(math.atan2(relative_y, relative_x)) % 360
        else:
            enemy_data['direction'] = enemy_data['direction']

        direction_radians = math.radians(enemy_data['direction'])
        new_x = (enemy_pos[0] + enemy_data['speed'] * math.cos(direction_radians)) % MAP_SIZE
        new_y = (enemy_pos[1] + enemy_data['speed'] * math.sin(direction_radians)) % MAP_SIZE
        
        # 새 위치로 적 정보 이동
        enemy_visibility[(new_x, new_y)] = enemy_data
        del enemy_visibility[enemy_pos]

        # 적의 맵 좌표를 플레이어 기준으로 상대 좌표로 변환
        relative_x = (new_x - player_x + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        relative_y = (new_y - player_y + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2

        # 적과 레이더 선이 닿는지 계산
        angle_to_enemy = math.degrees(math.atan2(relative_y, relative_x)) % 360
        distance_to_enemy = math.sqrt(relative_x**2 + relative_y**2)

        # 적이 레이더 범위 내에 있고 레이더 선이 적을 지나가면 보이도록 설정
        if distance_to_enemy <= RADAR_RADIUS and abs(radar_angle - angle_to_enemy) < 5:
            # 적이 레이더 범위 내에 있을 때 알파 값을 255로 설정
            enemy_data = enemy_visibility.get((new_x, new_y))
            if enemy_data:
                enemy_data['timer'] = time.time()  # 타이머 시작
                enemy_data['alpha'] = 255
                if (new_x, new_y) not in detected_enemies:
                    detected_enemies.append((new_x, new_y))

        # 적의 표시 시간 관리(2초 뒤 사라짐)
        if enemy_visibility[(new_x, new_y)]['timer'] is not None:
            elapsed_time = time.time() - enemy_visibility[(new_x, new_y)]['timer']
            if elapsed_time < 2:
                alpha = max(255 - int((elapsed_time / 2) * 255), 0)
                enemy_visibility[(new_x, new_y)]['alpha'] = alpha
            else:
                enemy_visibility[(new_x, new_y)]['alpha'] = 0
                enemy_visibility[(new_x, new_y)]['timer'] = None
                
                if (new_x, new_y) in detected_enemies:
                    detected_enemies.remove((new_x, new_y))

        # 적이 투명도가 0 이상일 때만 레이더에 표시
        if enemy_visibility[(new_x, new_y)]['alpha'] > 0:
            screen_x = CENTER_X + relative_x
            screen_y = CENTER_Y + relative_y
            direction_radians = math.radians(enemy_data['direction'])

            # 적 크기
            enemy_size = 15

            # 적 삼각형 모양
            triangle_points = [
                (screen_x + enemy_size * math.cos(direction_radians), screen_y + enemy_size * math.sin(direction_radians)),
                (screen_x + (enemy_size / 2) * math.cos(direction_radians + 2.5), screen_y + (enemy_size / 2) * math.sin(direction_radians + 2.5)),
                (screen_x + (enemy_size / 2) * math.cos(direction_radians - 2.5), screen_y + (enemy_size / 2) * math.sin(direction_radians - 2.5))
            ]

            # 적을 그릴 때 투명도 적용
            temp_surface = pygame.Surface((2 * enemy_size, 2 * enemy_size), pygame.SRCALPHA)
            pygame.draw.polygon(temp_surface, (*RED, enemy_visibility[(new_x, new_y)]['alpha']), 
                                 [(p[0] - screen_x + enemy_size, p[1] - screen_y + enemy_size) for p in triangle_points])
            if(battery_percentage>0):
                screen.blit(temp_surface, (screen_x - enemy_size, screen_y - enemy_size))

            if distance_to_player < PLAYER_RADIUS + 15: #적에 닿으면 게임 오버 [중심 거리 계산 aabb method2?]
                # 화면 좌표로 변환
                screen_x = CENTER_X + relative_x
                screen_y = CENTER_Y + relative_y

                # 날 죽인 적 표시 
                temp_surface = pygame.Surface((30, 30), pygame.SRCALPHA)  # 적의 크기 조절
                temp_surface.set_alpha(enemy_data['alpha'])  # 투명도 적용
                screen.blit(temp_surface, (screen_x - 15, screen_y - 15))  # 적을 화면에 그리기

                # 플레이어가 죽었을 때
                player_speed = 0
                pygame.display.flip()  # 화면 업데이트
                time.sleep(1)  # 1초 대기
                game_over = True  # 게임 오버 상태로 변경



    # 블랙홀 적 이동 및 레이더 감지
    for enemy_pos in list(blueenemy_visibility.keys()):
        enemy_data = blueenemy_visibility[enemy_pos]
    
        # 적과 플레이어 사이의 상대 위치 계산
        relative_x = (enemy_pos[0] - player_x + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        relative_y = (enemy_pos[1] - player_y + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2

        # 거리 계산
        distance_to_player = math.sqrt(relative_x**2 + relative_y**2)
    
        if distance_to_player < 120 and not breath_control: #한번 바뀌면 유지
            blackhole[enemy_pos] = 1
            blackhole_sound.play()
            enemy_data['speed'] = 0.0001
            enemy_data['is_blackhole'] = True
        else:
            blackhole[enemy_pos] = 0
            
        if enemy_data['is_blackhole'] == True:
            blackhole[enemy_pos] = 1
            sound_distance = min(distance_to_player, 1000)
            volume = max(0.1, (1000 - sound_distance) / 1000)
            blackhole_sound2.set_volume(volume)  
            blackhole_sound2.play()

        vector_field = {}

        #블랙홀 계산 [벡터필드]
        if blackhole[enemy_pos] == 1:
            # 서큘러 방식으로 상대 위치 계산
            relative_x = (enemy_pos[0] - player_x + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
            relative_y = (enemy_pos[1] - player_y + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
    
            distance_to_player = math.sqrt(relative_x**2 + relative_y**2)
    
            if distance_to_player < 1000:  #특정 범위에 영향을 미침
                if distance_to_player > 0:  # 0으로 나누기 방지
                    force_x = relative_x / distance_to_player  # x 방향 힘
                    force_y = relative_y / distance_to_player  # y 방향 힘
            
                    # 힘을 적용하여 플레이어 위치 변경
                    force_magnitude = 0.8  # 힘의 크기를 조정(움직이는데 제약이 생기는 정도, 아예 패널티가 크면 안됨)
                    player_x += force_x * force_magnitude
                    player_y += force_y * force_magnitude

        

        direction_radians = math.radians(enemy_data['direction'])
        new_x = (enemy_pos[0] + enemy_data['speed'] * math.cos(direction_radians)) % MAP_SIZE
        new_y = (enemy_pos[1] + enemy_data['speed'] * math.sin(direction_radians)) % MAP_SIZE
        
        # 새 위치로 적 정보 이동
        blueenemy_visibility[(new_x, new_y)] = enemy_data
        del blueenemy_visibility[enemy_pos]

        # 적의 맵 좌표를 플레이어 기준으로 상대 좌표로 변환
        relative_x = (new_x - player_x + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        relative_y = (new_y - player_y + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2

        # 적과 레이더 선이 닿는지 계산
        angle_to_enemy = math.degrees(math.atan2(relative_y, relative_x)) % 360
        distance_to_enemy = math.sqrt(relative_x**2 + relative_y**2)

        # 적이 레이더 범위 내에 있고 레이더 선이 적을 지나가면 보이도록 설정
        if distance_to_enemy <= RADAR_RADIUS and abs(radar_angle - angle_to_enemy) < 3:
            blueenemy_visibility[(new_x, new_y)]['timer'] = time.time()
            blueenemy_visibility[(new_x, new_y)]['alpha'] = 255
            
            if (new_x, new_y) not in detected_enemies:
                detected_enemies.append((new_x, new_y))

        # 적의 표시 시간 관리(2초 뒤 사라짐)
        if blueenemy_visibility[(new_x, new_y)]['timer'] is not None:
            elapsed_time = time.time() - blueenemy_visibility[(new_x, new_y)]['timer']
            if elapsed_time < 2:
                alpha = max(255 - int((elapsed_time / 2) * 255), 0)
                blueenemy_visibility[(new_x, new_y)]['alpha'] = alpha
            else:
                blueenemy_visibility[(new_x, new_y)]['alpha'] = 0
                blueenemy_visibility[(new_x, new_y)]['timer'] = None
                
                if (new_x, new_y) in detected_enemies:
                    detected_enemies.remove((new_x, new_y))

        # 적이 투명도가 0 이상일 때만 레이더에 표시
        if blueenemy_visibility[(new_x, new_y)]['alpha'] > 0:
            screen_x = CENTER_X + relative_x
            screen_y = CENTER_Y + relative_y
            direction_radians = math.radians(enemy_data['direction'])

            # 적 크기
            enemy_size = 15

            # 적 삼각형 모양
            triangle_points = [
                (screen_x + enemy_size * math.cos(direction_radians), screen_y + enemy_size * math.sin(direction_radians)),
                (screen_x + (enemy_size / 2) * math.cos(direction_radians + 2.5), screen_y + (enemy_size / 2) * math.sin(direction_radians + 2.5)),
                (screen_x + (enemy_size / 2) * math.cos(direction_radians - 2.5), screen_y + (enemy_size / 2) * math.sin(direction_radians - 2.5))
            ]

            # 적을 그릴 때 투명도 적용
            temp_surface = pygame.Surface((2 * enemy_size, 2 * enemy_size), pygame.SRCALPHA)
            radius = 10
            if blackhole[enemy_pos] == 0:
                color = GREEN
                pygame.draw.polygon(temp_surface, (*color, blueenemy_visibility[(new_x, new_y)]['alpha']), 
                                 [(p[0] - screen_x + enemy_size, p[1] - screen_y + enemy_size) for p in triangle_points])
            else:
                color = BLUE
                pygame.draw.circle(temp_surface, (*color, blueenemy_visibility[(new_x, new_y)]['alpha']),
                   (enemy_size, enemy_size), radius)
            if(battery_percentage>0):
                screen.blit(temp_surface, (screen_x - enemy_size, screen_y - enemy_size))

            if distance_to_player < PLAYER_RADIUS + 15: #적에 닿으면 게임 오버 [중심 거리 계산 aabb method2?]
                # 화면 좌표로 변환
                screen_x = CENTER_X + relative_x
                screen_y = CENTER_Y + relative_y

                # 날 죽인 적 표시 
                temp_surface = pygame.Surface((30, 30), pygame.SRCALPHA)  # 적의 크기 조절
                temp_surface.set_alpha(enemy_data['alpha'])  # 투명도 적용
                screen.blit(temp_surface, (screen_x - 15, screen_y - 15))  # 적을 화면에 그리기

                # 플레이어가 죽었을 때
                player_speed = 0
                pygame.display.flip()  # 화면 업데이트
                time.sleep(1)  # 1초 대기
                game_over = True  # 게임 오버 상태로 변경


    #게임 승리 조건
    if items_collected >= NUM_ITEMS: #아이탬 다 먹었으면
        relative_x = (spaceship_x - player_x + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        relative_y = (spaceship_y - player_y + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        distance_to_spaceship = math.sqrt(relative_x**2 + relative_y**2)

        if distance_to_spaceship < 15:  # 플레이어가 우주선에 닿으면
            screen.fill(BLACK)
            font = pygame.font.SysFont(None, 55)
            text_surface = font.render("You Win!", True, WHITE)
            screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, SCREEN_HEIGHT // 2 - text_surface.get_height() // 2))
            pygame.display.flip()
            time.sleep(2)  # 2초 대기
            running = False  # 게임 종료

    # 아이템 표시
    for item in items[:]:
        relative_x = (item[0] - player_x + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        relative_y = (item[1] - player_y + MAP_SIZE) % MAP_SIZE - MAP_SIZE // 2
        if -RADAR_RADIUS < relative_x < RADAR_RADIUS and -RADAR_RADIUS < relative_y < RADAR_RADIUS:
            screen_x = CENTER_X + relative_x
            screen_y = CENTER_Y + relative_y
            pygame.draw.circle(screen, YELLOW, (int(screen_x), int(screen_y)), 5)

            # 아이템 획득 처리[히트박스]
            distance_to_item = math.sqrt(relative_x**2 + relative_y**2)
            if distance_to_item < PLAYER_RADIUS + 5: 
                items_collected += 1
                items.remove(item)

    # 플레이어는 항상 중앙에 고정되어 그리기
    pygame.draw.circle(screen, WHITE, (CENTER_X, CENTER_Y), PLAYER_RADIUS)

    # 호흡 게이지 표시 (오른쪽 아래)
    pygame.draw.rect(screen, LIGHT_BLUE, (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 40, 100, 20))
    pygame.draw.rect(screen, (0, 0, 255), (SCREEN_WIDTH - 120, SCREEN_HEIGHT - 40, breath_gauge, 20))

    # 배터리 게이지 표시 (왼쪽 아래)
    pygame.draw.rect(screen, LIGHT_BLUE, (20, SCREEN_HEIGHT - 40, 100, 20))
    pygame.draw.rect(screen, (0, 255, 0), (20, SCREEN_HEIGHT - 40, battery_percentage, 20))

    # 아이템 카운트 표시
    item_count_text = f"{items_collected}/{NUM_ITEMS}"
    font = pygame.font.SysFont(None, 30)
    text_surface = font.render(item_count_text, True, WHITE)
    screen.blit(text_surface, (SCREEN_WIDTH - 120, 10))

    # 게임 종료 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    #게임 루프 내에서 키 입력 처리 수정
    keys = pygame.key.get_pressed()
    player_running = False

    speed_multiplier = 1

    # 걷기 및 달리기 처리 [Chord: Simultaneous Input]
    if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and can_recover_breath:
        if not breath_control:
            current_speed += acceleration 
            current_speed = min(current_speed, max_speed)  # 최대 속도 제한

            if keys[pygame.K_w]:
                player_y = (player_y - current_speed) % MAP_SIZE
                player_running = True
            if keys[pygame.K_s]:
                player_y = (player_y + current_speed) % MAP_SIZE
                player_running = True
            if keys[pygame.K_a]:
                player_x = (player_x - current_speed) % MAP_SIZE
                player_running = True
            if keys[pygame.K_d]:
                player_x = (player_x + current_speed) % MAP_SIZE
                player_running = True

            breath_gauge -= breath_depletion_rate * (2 if current_speed > player_speed else 1)
    else:
        # 감속 처리[미끄러짐 효과]
        if current_speed > 0:
            current_speed -= deceleration
            current_speed = max(current_speed, 0.1)  # 최소 속도 설정 (0.1로 설정)
        else:
            current_speed = 0 # 속도가 0 이하로 내려가면 0으로 설정
        #걷기 처리
        if not breath_control:
            if keys[pygame.K_w]:
                player_y = (player_y - player_speed) % MAP_SIZE
            if keys[pygame.K_s]:
                player_y = (player_y + player_speed) % MAP_SIZE
            if keys[pygame.K_a]:
                player_x = (player_x - player_speed) % MAP_SIZE
            if keys[pygame.K_d]:
                player_x = (player_x + player_speed) % MAP_SIZE

    # 걷기 소리 재생 함수 호출
    if player_running or (keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d]):
        walksound(player_running)
    # 숨을 참는 경우 (Ctrl을 눌렀을 때 이동 불가)
    if (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and can_recover_breath == True:
        if (current_time - heart_sound_timer >= heart_sound_interval) and breath_gauge > 0:
            breath_control_sound.play()
            heart_sound_timer = current_time  # 타이머 리셋
        if not player_running:
            breath_gauge -= breath_depletion_rate
            breath_control = True
    else:
        if can_recover_breath:
            breath_gauge += breath_recovery_rate
        breath_control = False
    

    temp_speed = rotation_speed
    # 배터리 소모 처리
    if not game_over:  
        battery_percentage -= battery_depletion_rate * clock.get_time() / 1000
        battery_percentage = max(min(battery_percentage, 100), 0)  # 배터리 비율을 0~100으로 제한

    # 스페이스바를 눌렀을 때 레이더 속도 2배
    if keys[pygame.K_SPACE]:
        rotation_speed = 360 / 1500  # 레이더 속도를 2배로 증가
        battery_percentage -= battery_depletion_rate * clock.get_time() / 1000 # 줄어드는 속도도 2배
    else:
        rotation_speed = 360 / 3000  # 원래 속도로 복구

    # 속도 조절
    if slow_speed_timer > 0:
        can_recover_breath = False
        slow_speed_timer -= clock.get_time() / 1000
        if slow_speed_timer <= 0:
            player_speed = 2
            can_recover_breath = True
    
    if breath_timer > 0:
        can_recover_breath = False
        breath_timer -= clock.get_time() / 1000
        if breath_timer <= 0:
            can_recover_breath = True

    # 달리는 중간에 게이지가 다 달면 이동속도 감소 및 회복 불가
    if player_running and breath_gauge <= 0:
        player_speed = 1
        slow_speed_timer = 3
        running_sound.play()

    # 숨을 참는 중간에 게이지가 다 달면 회복 불가
    if breath_control and breath_gauge <= 0:
        breath_timer = 2

    # 호흡 게이지가 0 이하로 떨어지지 않도록 제한
    breath_gauge = max(min(breath_gauge, 100), 0)

    pygame.display.flip()
     # [프레임 60고정]
    clock.tick(60)
    

pygame.quit()
