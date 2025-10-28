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
BLOCK_WIDTH = 75   # ブロックの横幅
BLOCK_HEIGHT = 30  # ブロックの縦幅
FPS = 60           # フレームレート

# 色の定義 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

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
    """ ラケット（操作対象）のクラス """
    def __init__(self):
        # ラケットのRectを画面中央下に作成
        self.rect = pg.Rect(
            (SCREEN_WIDTH - PADDLE_WIDTH) // 2, 
            SCREEN_HEIGHT - PADDLE_HEIGHT - 20, 
            PADDLE_WIDTH, 
            PADDLE_HEIGHT
        )
        self.speed = 10 # 移動速度

    def update(self, keys):
        """ キー入力に基づきラケットを移動 """
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
        """ ラケットを画面に描画 """
        pg.draw.rect(screen, BLUE, self.rect)

class Ball:
    """ ボールのクラス """
    def __init__(self):
        # ボールのRectをラケットの少し上に作成
        self.rect = pg.Rect(
            SCREEN_WIDTH // 2 - BALL_RADIUS, 
            SCREEN_HEIGHT - PADDLE_HEIGHT - 50, 
            BALL_RADIUS * 2, 
            BALL_RADIUS * 2
        )
        # ボールの速度（x方向, y方向）
        self.vx = random.choice([-5, 5])
        self.vy = -5
        self.speed = 5

    def update(self, paddle, blocks, particles, break_sound=None):
        """ ボールの移動と衝突判定 """
        self.rect.move_ip(self.vx, self.vy)

        # 壁との衝突判定 (上)
        if self.rect.top < 0:
            self.vy *= -1 # Y方向の速度を反転
            self.rect.top = 0

        # 壁との衝突判定 (左・右)
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.vx *= -1 # X方向の速度を反転
            if self.rect.left < 0: self.rect.left = 0
            if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

        # ラケットとの衝突判定
        if self.rect.colliderect(paddle.rect):
            self.vy *= -1 # Y方向の速度を反転
            self.rect.bottom = paddle.rect.top # めり込まないように位置調整
            
            # ラケットの当たった位置で反射角度を変える（簡易的）
            center_diff = self.rect.centerx - paddle.rect.centerx
            self.vx = (center_diff / (PADDLE_WIDTH / 2)) * self.speed
            # vxが0に近すぎるとループするので最小値を設定
            if abs(self.vx) < 1:
                self.vx = 1 if self.vx >= 0 else -1


        # ブロックとの衝突判定
        collided_block = self.rect.collidelist(blocks) # どのブロックと衝突したか
        if collided_block != -1: # -1以外は衝突
            block = blocks.pop(collided_block) # 衝突したブロックをリストから削除
            
            # ボールの反射処理（簡易的にY方向のみ反転）
            # 実際にはブロックの上下左右どこに当たったか判定すべきだが簡略化
            self.vy *= -1
            
            # パーティクルエフェクトの生成（衝突したブロックの中心から）
            for _ in range(10):  # 10個のパーティクルを生成
                particles.append(
                    Particle(block.centerx, block.centery, (*WHITE, 255))
                )
            
            # 効果音の再生
            if break_sound is not None:
                break_sound.play()
            
            return True # ブロックに当たった
        
        return False # ブロックに当たらなかった

    def draw(self, screen):
        """ ボールを画面に描画 (円形) """
        pg.draw.circle(screen, WHITE, self.rect.center, BALL_RADIUS)

    def is_out_of_bounds(self):
        """ ボールが画面下に落ちたか判定 """
        return self.rect.top > SCREEN_HEIGHT


class Block(pg.Rect):
    """ ブロックのクラス (pg.Rectを継承) """
    def __init__(self, x, y, color):
        super().__init__(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)
        self.color = color

    def draw(self, screen):
        """ ブロックを画面に描画 """
        pg.draw.rect(screen, self.color, self)

# --- メイン処理 ---

def create_block_row(y: int) -> list[Block]:
    """
    指定のy座標にブロックの新しい1行を生成
    引数 y: ブロックのy座標
    戻り値: 生成したブロックのリスト
    """
    new_blocks = []
    for x in range(10):  # 10列
        block = Block(
            x * (BLOCK_WIDTH + 5) + 20,  # X座標 (隙間5px, 左マージン20px)
            y,  # 指定されたY座標
            WHITE  # 白色で統一
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
    # 講義資料 P.8 のお作法 
    # (画像など外部ファイルを読み込む際にパスの基準を固定する)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Pygameの初期化
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("ブロック崩し")
    clock = pg.time.Clock()
    font = pg.font.Font(None, 50) # スコア表示用フォント
    
    # 効果音のロード
    sounds = load_sounds()

    # オブジェクトのインスタンス化
    paddle = Paddle()
    ball = Ball()
    blocks = []
    particles = []  # パーティクルのリストを追加
    
    # 初期ブロックの配置（4行）
    for y in range(4):
        blocks.extend(create_block_row(y * (BLOCK_HEIGHT + 5) + 30))

    score = 0
    game_over = False
    game_clear = False
    
    # ブロック移動の管理用変数
    last_drop_time = time.time()  # 最後にブロックを落とした時刻
    DROP_INTERVAL = 10  # ブロックを落とす間隔（秒）

    # ゲームループ
    while True:
        # イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r and (game_over or game_clear):
                    # ゲームオーバーかクリア時にRキーでリスタート
                    main() # main関数を再帰呼び出ししてリセット
                    return

        if not game_over and not game_clear:
            # キー入力の取得
            keys = pg.key.get_pressed()
            
            # オブジェクトの更新
            paddle.update(keys)
            if ball.update(paddle, blocks, particles, sounds.get("break")): # ブロックに当たったら
                score += 10 # スコア加算

            # パーティクルの更新
            particles[:] = [p for p in particles if p.update()]

            # ゲームオーバー判定
            if ball.is_out_of_bounds():
                game_over = True
                # ゲームオーバー効果音を再生
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
            if not blocks: # ブロックがなくなったら
                game_clear = True

        # 描画処理
        screen.fill(BLACK) # 背景を黒で塗りつぶし
        
        # ゲームオーバーラインを描画（点線で表示）
        dash_length = 15  # 点線の長さ
        gap_length = 10   # 点線の間隔
        for x in range(0, SCREEN_WIDTH, dash_length + gap_length):
            pg.draw.line(screen, RED, (x, GAME_OVER_LINE), (x + dash_length, GAME_OVER_LINE), 2)
            
        paddle.draw(screen)
        ball.draw(screen)
        for block in blocks:
            block.draw(screen)
        
        # パーティクルの描画
        for particle in particles:
            particle.draw(screen)

        # スコア表示
        score_text = font.render(f"SCORE: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # ゲームオーバー / クリア表示
        if game_over:
            msg_text = font.render("GAME OVER", True, RED)
            screen.blit(msg_text, (SCREEN_WIDTH // 2 - msg_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            msg_text2 = font.render("Press 'R' to Restart", True, WHITE)
            screen.blit(msg_text2, (SCREEN_WIDTH // 2 - msg_text2.get_width() // 2, SCREEN_HEIGHT // 2))
        
        if game_clear:
            msg_text = font.render("GAME CLEAR!", True, YELLOW)
            screen.blit(msg_text, (SCREEN_WIDTH // 2 - msg_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            msg_text2 = font.render("Press 'R' to Restart", True, WHITE)
            screen.blit(msg_text2, (SCREEN_WIDTH // 2 - msg_text2.get_width() // 2, SCREEN_HEIGHT // 2))


        # 画面の更新
        pg.display.update()
        
        # フレームレートの制御
        clock.tick(FPS)

if __name__ == "__main__":
    main()