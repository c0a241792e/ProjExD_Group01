import pygame as pg
import sys
import os
import random
import time
import math  # 標準のmathモジュールを追加

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 定数設定 ---
SCREEN_WIDTH = 800  # 画面の横幅
SCREEN_HEIGHT = 600 # 画面の縦幅
PADDLE_WIDTH = 100 # ラケットの横幅
PADDLE_HEIGHT = 20 # ラケットの縦幅
BALL_RADIUS = 10   # ボールの半径
BLOCK_WIDTH = 69   # ブロックの横幅
BLOCK_HEIGHT = 30  # ブロックの縦幅
FPS = 60           # フレームレート

# 色定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (200, 0, 200)
# ★担当アイテムの色
PINK = (255, 192, 203) # ラケット巨大化
ORANGE = (255, 165, 0) # 残機増加
CYAN = (0, 255, 255)   # ボール増加

# ゲームオーバーラインのY座標（ラケットの少し上）
GAME_OVER_LINE = SCREEN_HEIGHT - 150

# パーティクルの設定
PARTICLE_LIFETIME = 30  # パーティクルの寿命（フレーム数）
PARTICLE_SPEED = 5     # パーティクルの初期速度

# --- サウンド設定 ---
def load_sounds():
    """効果音をロード"""
    pg.mixer.init()  # mixer（音声周り）の初期化
    sounds = {}
    try:
        # ブロック破壊音
        break_sound = pg.mixer.Sound("sound/break.mp3")
        break_sound.set_volume(0.4)  # 音量を40%に設定
        sounds["break"] = break_sound
        
        # ゲームオーバー音
        defeat_sound = pg.mixer.Sound("sound/defeat.mp3")
        defeat_sound.set_volume(0.5)  # 音量を50%に設定
        sounds["defeat"] = defeat_sound
        
    except Exception as e:
        print(f"効果音ファイルの読み込みに失敗しました: {e}")
    
    return sounds
PURPLE = (200, 0, 200)
ORANGE = (255, 120, 0)

HP3_PROBABILITY = 0.10 # 10%の確率でHP 3 (超高耐久・超高得点)
HP2_PROBABILITY = 0.20 # 20%の確率でHP 2 (高耐久・高得点)

# --- クラス定義 ---

class Particle:
    """パーティクルエフェクトのクラス"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = PARTICLE_LIFETIME
        # ランダムな方向と速度を設定
        angle = random.uniform(0, 2 * math.pi)  # ランダムな角度（0-2π）
        speed = random.uniform(2, PARTICLE_SPEED)
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.size = random.randint(2, 4)  # パーティクルのサイズ

    def update(self):
        """パーティクルの位置と寿命を更新"""
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        # 徐々に透明になる
        alpha = int(255 * (self.lifetime / PARTICLE_LIFETIME))
        self.color = (*self.color[:3], alpha)
        return self.lifetime > 0

    def draw(self, screen):
        """パーティクルを描画"""
        particle_surface = pg.Surface((self.size * 2, self.size * 2), pg.SRCALPHA)
        pg.draw.circle(particle_surface, self.color, (self.size, self.size), self.size)
        screen.blit(particle_surface, (int(self.x) - self.size, int(self.y) - self.size))

class Paddle:
    def __init__(self):
        self.rect = pg.Rect(
            (SCREEN_WIDTH - PADDLE_WIDTH) // 2,
            SCREEN_HEIGHT - PADDLE_HEIGHT - 20,
            PADDLE_WIDTH,
            PADDLE_HEIGHT
        )
        self.speed = 10

    def update(self, keys):
        if keys[pg.K_a]:
            self.rect.move_ip(-self.speed, 0)
        if keys[pg.K_d]:
            self.rect.move_ip(self.speed, 0)
        
        # 画面外に出ないように制限
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def draw(self, screen):
        pg.draw.rect(screen, BLUE, self.rect)

class Ball:
    """ ボールのクラス (基本機能) """
    def __init__(self):
        # ... (既存の rect, vx, vy, speed の設定はそのまま) ...
        self.rect = pg.Rect(
            SCREEN_WIDTH // 2 - BALL_RADIUS,
            SCREEN_HEIGHT - PADDLE_HEIGHT - 50,
            BALL_RADIUS * 2,
            BALL_RADIUS * 2
        )
        self.vx = random.choice([-5, 5])
        self.vy = -5
        self.speed = 5

        # --- ▼ アイテム効果用の変数を追加 ▼ ---
        self.penetrate = False # 貫通状態か
        self.penetrate_timer = 0 # 貫通の持続時間タイマー
        self.is_large = False  # 巨大化状態か
        self.large_timer = 0   # 巨大化の持続時間タイマー
        # --- ▲ -------------------------- ▲ ---

    def update(self, paddle, blocks, particles, break_sound=None):
        """ ボールの移動と衝突判定 """
        self.rect.move_ip(self.vx, self.vy)

        # 壁との衝突 (上)
        if self.rect.top < 0:
            self.vy *= -1 
            self.rect.top = 0

        # 壁との衝突 (左・右)
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.vx *= -1 
            if self.rect.left < 0: self.rect.left = 0
            if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

        # ラケットとの衝突
        if self.rect.colliderect(paddle.rect):
            self.vy *= -1 
            self.rect.bottom = paddle.rect.top 
            
            # ラケット幅の変動に対応 (item1)
            center_diff = self.rect.centerx - paddle.rect.centerx
            self.vx = (center_diff / (paddle.rect.width / 2)) * self.speed 
            if abs(self.vx) < 1:
                self.vx = 1 if self.vx >= 0 else -1

            # --- ▼ 貫通アイテムの効果がラケットで切れるようにする（任意）▼ ---
            # if self.penetrate:
            #     self.set_penetrate(False) # ラケットに当たったら貫通解除する場合
            # --- ▲ --------------------------------------------------- ▲ ---


        # ブロックとの衝突判定
        collided_index = self.rect.collidelist(blocks) 
        if collided_index != -1: 
            # 💡 (1) 衝突したブロックをインデックスで削除し、blockに代入
            block = blocks.pop(collided_index) 
            
            # --- ▼ 貫通状態の処理 ▼ ---
            if self.penetrate:
                # 貫通状態なら反射しない (ブロックは消えるだけ)
                is_destroyed = True # 貫通状態では即座に破壊と見なす
            else:
                # 通常時は反射する
                self.vy *= -1

                # ブロックの耐久度を減らす
                block.hp -= 1
                
                # 💡 (2) 破壊されたかどうかを判定
                if block.hp <= 0:
                    is_destroyed = True
                else:
                    is_destroyed = False
                    
                    # 💡 (3) HPが残っている場合は、ブロックをリストに戻し、処理を終了
                    blocks.insert(collided_index, block)
                    return False, None # 破壊されていない

            # 💡 (4) ブロックが破壊された（is_destroyed = True）場合のみ、以下の処理を実行
            if is_destroyed:
                hit_score = block.score_value # スコアを取得
                
                # パーティクルエフェクトの生成（衝突したブロックの中心から）
                for _ in range(10):  # 10個のパーティクルを生成
                    particles.append(
                        Particle(block.centerx, block.centery, (*WHITE, 255))
                    )
                
                # 効果音の再生
                if break_sound is not None:
                    break_sound.play()
                
                return True, block # ブロックに当たったこと（破壊）と、壊したブロックを返すd
        
        # --- ▼ アイテムタイマーの更新 ▼ ---
        if self.is_large:
            self.large_timer -= 1
            if self.large_timer <= 0:
                self.set_size(False) # 通常サイズに戻す
        
        if self.penetrate:
            self.penetrate_timer -= 1
            if self.penetrate_timer <= 0:
                self.set_penetrate(False) # 通常状態に戻す
        # --- ▲ ---------------------- ▲ ---
        
        # --- ▼ 戻り値を変更 ▼ ---
        return False, None # ブロックに当たらなかった


    def draw(self, screen):
        """ ボールを画面に描画 (円形) """
        # --- ▼ 状態に応じて描画を変更 ▼ ---
        radius = BALL_RADIUS * 2 if self.is_large else BALL_RADIUS
        color = GREEN if self.penetrate else WHITE
        pg.draw.circle(screen, color, self.rect.center, radius)
        # --- ▲ ------------------------- ▲ ---

    def is_out_of_bounds(self):
        return self.rect.top > SCREEN_HEIGHT

    # --- ▼ アイテム効果を適用するメソッドを追加 ▼ ---
    def set_penetrate(self, value):
        """ 貫通状態を設定する """
        self.penetrate = value
        if value:
            self.penetrate_timer = 60 * 10 # 10秒間持続 (FPS=60)
        else:
            self.penetrate_timer = 0

    def set_size(self, is_large):
        """ ボールのサイズを変更する """
        # サイズ変更時に中心がズレないように調整
        center = self.rect.center
        
        self.is_large = is_large
        if is_large:
            # 巨大化
            self.rect.width = BALL_RADIUS * 4
            self.rect.height = BALL_RADIUS * 4
            self.large_timer = 60 * 10 # 10秒間持続 (FPS=60)
        else:
            # 通常化
            self.rect.width = BALL_RADIUS * 2
            self.rect.height = BALL_RADIUS * 2
        
        self.rect.center = center # 中心を再設定

class Block(pg.Rect):
    """ ブロックのクラス (pg.Rectを継承) """
    def __init__(self, x, y, color, hp=1, score_value=10):
        super().__init__(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)
        self.max_hp = hp      # 最大耐久度
        self.hp = hp          # 現在の耐久度
        self.color = color    # 現在の色a
        self.base_color = color # 元の色
        self.score_value = score_value # 破壊時の得点

    def draw(self, screen):
        #pg.draw.rect(screen, self.color, self)
        """ ブロックを画面に描画 """
        if self.hp > 1:
            color_to_draw = self.base_color
            if self.hp == 2:
                color_to_draw = ORANGE
            elif self.hp > 2:
                color_to_draw = RED 
        else:
            color_to_draw = self.base_color
        
        pg.draw.rect(screen, color_to_draw, self)
        if self.hp > 1:
            pg.draw.rect(screen, WHITE, self, 3)
         

class item1:
    """
    担当アイテムの効果発動とタイマー管理を行うクラス
    (ラケット巨大化、残機増加、ボール増加)
    """
    def __init__(self, paddle_original_width):
        self.paddle_extend_active = False
        self.extend_start_time = 0
        self.EXTEND_DURATION = 10000 # 10秒 = 10000 ms
        self.original_width = paddle_original_width
        self.extended_width = int(paddle_original_width * 1.5) 

    def activate(self, effect_name: str, balls: list, paddle: Paddle) -> int:
        """
        アイテム名(effect_name)に基づき、効果を発動する。
        :return: 残機(life)の増減量 (int)
        """
        if effect_name == "extend_paddle": # ラケット巨大化
            self.paddle_extend_active = True
            self.extend_start_time = pg.time.get_ticks()
            center_x = paddle.rect.centerx
            paddle.rect.width = self.extended_width
            paddle.rect.centerx = center_x
            return 0 

        elif effect_name == "increase_life": # 残機増加
            return 1 # mainループ側でlifeを1増やす

        elif effect_name == "increase_ball": # ボール増加
            balls.append(Ball()) 
            return 0
        
        return 0 # 担当外のアイテム

    def update(self, paddle: Paddle):
        """
        毎フレーム呼び出す。ラケット巨大化のタイマーを管理する。
        """
        if not self.paddle_extend_active:
            return
        current_time = pg.time.get_ticks()
        elapsed_time = current_time - self.extend_start_time
        if elapsed_time > self.EXTEND_DURATION:
            self.paddle_extend_active = False
            center_x = paddle.rect.centerx
            paddle.rect.width = self.original_width
            paddle.rect.centerx = center_x

class Item(pg.Rect):
    """ 落下アイテムの共通クラス (pg.Rectを継承) """
    def __init__(self, x, y, item_type):
        self.item_type = item_type # "extend_paddle" など
        
        # 担当アイテムの色分け
        if self.item_type == "extend_paddle":
            self.color = PINK 
        elif self.item_type == "increase_life":
            self.color = ORANGE 
        elif self.item_type == "increase_ball":
            self.color = CYAN 
        elif item_type == "life_up":
            self.color = (255, 0, 0)        # 赤
        elif item_type == "large_ball":
            self.color = (0, 255, 0)        # 緑
        elif item_type == "penetrate":
            self.color = (255, 255, 0)      # 黄
        elif item_type == "bomb":
            self.color = (255, 100, 100)    # ピンク寄り
        elif item_type == "helper":
            self.color = (200, 0, 200)      # 紫
        else:
            self.color = (255, 255, 255)    # 未定義なら白
            
        self.speed = 3 # 落下速度
        item_width = 20
        item_height = 20
        super().__init__(x - item_width // 2, y - item_height // 2, item_width, item_height)

    def update(self):
        """ アイテムを下に移動させる """
        self.move_ip(0, self.speed)

    def draw(self, screen):
        """ アイテムを描画する（色分け） """
        pg.draw.rect(screen, self.color, self)

    def check_collision(self, paddle_rect):
        """ ラケットとの衝突を判定する """
        return self.colliderect(paddle_rect)



class Item2(pg.Rect):
    """ アイテムのクラス (pg.Rectを継承) """
    def __init__(self, x, y, item_type):
        self.item_type = item_type # "penetrate"（貫通） or "large_ball"（巨大化）
        
        # アイテムの種類によって色を変える
        if self.item_type == "penetrate":
            self.color = GREEN # 貫通アイテムは緑
        elif self.item_type == "large_ball":
            self.color = YELLOW # 巨大化アイテムは黄
        
        self.speed = 3 # 落下速度
        
        # アイテムのサイズ
        item_width = 20
        item_height = 20
        # (x, y) はブロックの中心座標として受け取り、アイテムの中心に設定する
        super().__init__(x - item_width // 2, y - item_height // 2, item_width, item_height)

    def update(self):
        """ アイテムを下に移動させる """
        self.move_ip(0, self.speed)

    def draw(self, screen):
        """ アイテムを描画する（色分け） """
        pg.draw.rect(screen, self.color, self)
    
    def check_collision(self, paddle_rect):
        """ ラケットとの衝突を判定する """
        return self.colliderect(paddle_rect)

# --- Item3：爆弾・助っ人こうかとん ---
class Item3:
    def __init__(self, x, y, item_type):
        self.item_type = item_type
        self.speed = 3
        self.active = False
        self.image = None
        size = 20
        self.rect = pg.Rect(x - size//2, y - size//2, size, size)
        self.vx = -7  # 右から左
        self.row_y = y
        self.life = 0
        self.color = RED if item_type == "bomb" else PURPLE

    def update(self, blocks=None):
        if not self.active:
            self.rect.move_ip(0, self.speed)
        else:
            self.rect.move_ip(self.vx, 0)
            if blocks:
                # 横方向で重なったブロックだけ削除
                for block in blocks[:]:
                    if abs(block.centery - self.row_y) < BLOCK_HEIGHT // 2 and \
                       block.left < self.rect.right and block.right > self.rect.left:
                        blocks.remove(block)
            self.life -= 1
            if self.life <= 0 or self.rect.right < 0:
                self.active = False

    def draw(self, screen):
        if self.active and self.image:
            screen.blit(self.image, self.rect)
        else:
            pg.draw.rect(screen, self.color, self.rect)

    def check_collision(self, paddle_rect):
        return self.rect.colliderect(paddle_rect)

    def activate(self, blocks):
        if self.item_type == "bomb":
            if not blocks: return
            target = random.choice(blocks)
            destroyed = []
            for block in blocks[:]:
                if abs(block.centerx - target.centerx) <= BLOCK_WIDTH + 5 and \
                   abs(block.centery - target.centery) <= BLOCK_HEIGHT + 5:
                    destroyed.append(block)
            for b in destroyed:
                blocks.remove(b)
        else:
            try:
                self.image = pg.image.load("koukaton.jpg")
                self.image = pg.transform.scale(self.image, (50, 50))
            except:
                self.image = None
            self.active = True
            self.life = 200
            # 一番上の行から右端に出現
            if blocks:
                rows = sorted(list(set(block.centery for block in blocks)))
                self.row_y = rows[0]
                self.rect.centery = self.row_y
            self.rect.right = SCREEN_WIDTH

# --- メイン処理 ---
def create_block_row(y: int) -> list[Block]:
    """
    指定のy座標にブロックの新しい1行を生成
    引数 y: ブロックのy座標
    戻り値: 生成したブロックのリスト
    """
    new_blocks = []
    base_color = WHITE 
    
    # グローバルな確率定数を使用

    for x in range(10):  # 10列
        hp = 1
        score_value = 10 
        rand_val = random.random()

        if rand_val < HP3_PROBABILITY:
            hp = 3
            score_value = 50
        elif rand_val < HP3_PROBABILITY + HP2_PROBABILITY:
            hp = 2
            score_value = 30
        else:
            hp = 1
            score_value = 10

        block = Block(
            x * (BLOCK_WIDTH + 8) + 20,  # X座標 (隙間5px, 左マージン20px)
            y,  # 指定されたY座標
            base_color, 
            hp=hp, 
            score_value=score_value
        )
        new_blocks.append(block)
    return new_blocks

def move_blocks_down(blocks: list[Block]) -> bool:
    """
    全てのブロックを1段下に移動
    引数 blocks: ブロックのリスト
    戻り値: ゲームオーバー（ブロックが下限に達したか）
    """
    for block in blocks:
        block.y += BLOCK_HEIGHT + 5  # ブロック1個分（+隙間）下に移動
        if block.bottom >= GAME_OVER_LINE:  # ゲームオーバーライン
            return True
    return False

def main():
    """ メインのゲームループ """
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Pygameの初期化
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("ウォールブレイカー")
    clock = pg.time.Clock()
    font = pg.font.Font(None, 50) 
    
    # 効果音のロード
    sounds = load_sounds()

    paddle = Paddle()
    
    # ボールはリスト管理
    balls = [Ball()] 
    
    # 落下アイテムリスト
    items = [] 

    item3_list = []
    
    blocks = []
    
    # 担当アイテムマネージャー
    item_manager_ishii = item1(PADDLE_WIDTH) 
    particles = []  # パーティクルのリストを追加
    # --- ▼ アイテムリストを追加 ▼ ---
    items = [] # 落下中のアイテムを管理するリスト
    # --- ▲ ------------------- ▲ ---

    # ... (ブロックの配置 はそのまま) ...
    # block_colors = [RED, YELLOW, GREEN, BLUE]

    # HP3_PROBABILITY = 0.20 # 10%の確率でHP 3 (超高耐久・超高得点)
    # HP2_PROBABILITY = 0.30 # 20%の確率でHP 2 (高耐久・高得点)

    for y in range(4): 
        for x in range(10): 
            hp = 1
            score_value = 10 
            rand_val = random.random()

            if rand_val < HP3_PROBABILITY:
                hp = 3
                score_value = 50
            elif rand_val < HP3_PROBABILITY + HP2_PROBABILITY:
                hp = 2
                score_value = 30
            else:
                hp = 1
                score_value = 10
            color = WHITE
                
            block = Block(
                x * (BLOCK_WIDTH + 8) + 20, # <--- 隙間を広げ、配置を見やすく調整
                y * (BLOCK_HEIGHT + 5) + 30, 
                color,
                hp=hp,             
                score_value=score_value
            )
            blocks.append(block)

    score = 0
    life = 1
    game_over = False
    game_clear = False
    
    # ブロック移動の管理用変数
    last_drop_time = time.time()  # 最後にブロックを落とした時刻
    DROP_INTERVAL = 10  # ブロックを落とす間隔（秒）
    
    # (ダミー) 担当分のアイテムのみ抽選
    MY_ITEM_TYPES = [
        "extend_paddle", # item1
        "increase_life", # item1
        "increase_ball", # item1
        "large_ball",   # item2
        "penetrate",     # item2
        "bomb",          #item3
        "helper"        #item3
    ]

    # --- ゲームループ ---
    while True:
        # --- イベント処理 ---
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r and (game_over or game_clear):
                    main() # ゲームリスタート
                    return
                
                # --- デバッグキー (コメントアウト) ---
                # '1'キーでラケット巨大化アイテムを強制ドロップ
                # if event.key == pg.K_1:
                #     item = Item(SCREEN_WIDTH // 2, 0, "extend_paddle")
                #     items.append(item)
                # '2'キーで残機増加アイテムを強制ドロップ
                # elif event.key == pg.K_2:
                #     item = Item(SCREEN_WIDTH // 2, 0, "increase_life")
                #     items.append(item)
                # '3'キーでボール増加アイテムを強制ドロップ
                # elif event.key == pg.K_3:
                #     item = Item(SCREEN_WIDTH // 2, 0, "increase_ball")
                #     items.append(item)

        if not game_over and not game_clear:
            keys = pg.key.get_pressed()
            paddle.update(keys)
            # すべてのボールを更新
        for ball in balls[:]:
            # ブロック判定＋パーティクル＆音
            block_hit, destroyed_block = ball.update(paddle, blocks, particles, sounds.get("break"))

            if block_hit:  # ブロックに当たったら
                score += 10  # スコア加算

                # --- アイテムドロップ処理 (抽選処理のダミー) ---
                # 30%の確率で担当アイテムをドロップ
                if random.random() < 0.3: 
                    item_type = random.choice(MY_ITEM_TYPES)
                                    
                #item_typeに応じて生成するクラスを分ける
                    if item_type in ["penetrate", "large_ball"]:
                        item = Item2(destroyed_block.centerx, destroyed_block.centery, item_type)
                    else:
                        item = Item(destroyed_block.centerx, destroyed_block.centery, item_type)
                        
                    items.append(item) # アイテムをリストに追加
            

        # --- 落下アイテムの更新とラケットとの衝突判定 ---
        for item in items[:]: # リストのコピーをイテレート
            item.update() # アイテムを落下
                
            # ラケットと衝突したら
            if item.check_collision(paddle.rect):
                item_type = item.item_type # "extend_paddle" などを取得
                    
                # --- item1の効果発動 ---
                life_change = item_manager_ishii.activate(item_type, balls, paddle)
                life += life_change # 残機を更新
                if life > 5:
                    life = 5
                
                # --- item2の効果発動 ---
                if item_type in ["large_ball", "penetrate"]:
                    for ball in balls:
                        if item_type == "large_ball":
                            ball.set_size(True) # 巨大化
                        elif item_type == "penetrate":
                            ball.set_penetrate(True) # 貫通化 

                # --- item3の効果発動 ---
                if item_type in ["bomb", "helper"]:
                    # Item3のインスタンスを生成して効果発動
                    item3 = Item3(item.centerx, item.centery, item_type)
                    item3.activate(blocks)
                    item3_list.append(item3)

                items.remove(item) # アイテムをリストから削除
                
            # 画面外に出たら削除
            elif item.top > SCREEN_HEIGHT:
                items.remove(item)
            
        # ラケット巨大化タイマーの更新
        item_manager_ishii.update(paddle)
            
        # 画面外に落ちたボールをリストから削除
        balls = [ball for ball in balls if not ball.is_out_of_bounds()]

        # ボールが0個になったら残機を減らす
        if not balls and not game_clear and not game_over:
            life -= 1
            if life > 0:
                balls.append(Ball()) 
                paddle = Paddle() 
            else:
                if not game_over: 
                    game_over = True 
                    if sounds.get("defeat"):
                        sounds["defeat"].play()
            
        # ブロックの移動と新しい行の追加（5秒ごと）
        current_time = time.time()
        if current_time - last_drop_time >= DROP_INTERVAL:
            # 全ブロックを1段下に移動
            if move_blocks_down(blocks):
                game_over = True  # ブロックが下限に達したらゲームオーバー
                # ゲームオーバー効果音を再生
                if sounds.get("defeat"):
                    sounds["defeat"].play()
            else:
                # 最上段に新しい行を追加
                blocks.extend(create_block_row(30))  # 上端のY座標（30px）
            last_drop_time = current_time

        # ゲームクリア判定
        if not blocks:
            game_clear = True

        # 描画処理
        screen.fill(BLACK) 
        
        # ゲームオーバーラインを描画（点線で表示）
        dash_length = 15  # 点線の長さ
        gap_length = 10   # 点線の間隔
        for x in range(0, SCREEN_WIDTH, dash_length + gap_length):
            pg.draw.line(screen, RED, (x, GAME_OVER_LINE), (x + dash_length, GAME_OVER_LINE), 2)
            
        paddle.draw(screen)
        
        for ball in balls: # すべてのボールを描画
            ball.draw(screen)
        for block in blocks:
            block.draw(screen)
        
        # パーティクルの描画
        for particle in particles[:]:
            if particle.update():
                particle.draw(screen)
            else:
                particles.remove(particle)

        # --- ▼ アイテムの描画 ▼ ---
        for item in items:
            item.draw(screen)
        # --- ▲ ----------------- ▲ ---

        # --- Item3 の更新・描画 ---
        for i3 in item3_list[:]:
            i3.update(blocks)
            i3.draw(screen)
            if not i3.active and i3.rect.top > SCREEN_HEIGHT:
                item3_list.remove(i3)


        # ... (スコア表示、ゲームオーバー / クリア表示 はそのまま) ...
        score_text = font.render(f"SCORE: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        life_text = font.render(f"LIFE: {life}", True, WHITE)
        screen.blit(life_text, (SCREEN_WIDTH - life_text.get_width() - 10, 10))



        if game_over:
            over_text = font.render("GAME OVER - Press R to Restart", True, RED)
            screen.blit(over_text, (100, SCREEN_HEIGHT // 2))
        elif game_clear:
            clear_text = font.render("GAME CLEAR! - Press R to Restart", True, YELLOW)
            screen.blit(clear_text, (100, SCREEN_HEIGHT // 2))


        pg.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
