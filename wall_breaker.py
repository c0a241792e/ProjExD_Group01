import pygame as pg
import sys
import os
import random

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

# 色の定義 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 120, 0)

# --- クラス定義 ---

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

    def update(self, paddle, blocks):
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
        collided_index = self.rect.collidelist(blocks)
        if collided_index != -1:
            block = blocks[collided_index] # 衝突したブロックを取得
            
            # ボールの反射処理（簡易的にY方向のみ反転）
            self.vy *= -1
            
            # ブロックの耐久度を減らす
            block.hp -= 1
            
            hit_score = 0
            if block.hp <= 0:
                # 耐久度が0になったらリストから削除し、スコアを取得
                hit_score = block.score_value 
                blocks.pop(collided_index)
            else:
                # ブロックに当たったが破壊はしなかった
                hit_score = 0 # 破壊できなかったのでスコアは0

            return hit_score # ブロックを破壊した場合、そのブロックのスコアを返す

        return 0 # ブロックに当たらなかった

    def draw(self, screen):
        """ ボールを画面に描画 (円形) """
        pg.draw.circle(screen, WHITE, self.rect.center, BALL_RADIUS)

    def is_out_of_bounds(self):
        """ ボールが画面下に落ちたか判定 """
        return self.rect.top > SCREEN_HEIGHT


class Block(pg.Rect):
    """ ブロックのクラス (pg.Rectを継承) """
    def __init__(self, x, y, color, hp=1, score_value=10):
        super().__init__(x, y, BLOCK_WIDTH, BLOCK_HEIGHT)
        self.max_hp = hp      # 最大耐久度
        self.hp = hp          # 現在の耐久度
        self.base_color = color # 元の色
        self.score_value = score_value # 破壊時の得点

    def draw(self, screen):
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
            pg.draw.rect(screen, WHITE, self, 3) # 太さ3の白い枠線

# --- メイン処理 ---

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

    # オブジェクトのインスタンス化
    paddle = Paddle()
    ball = Ball()
    blocks = []
    
    # ブロックの配置
    block_colors = [GREEN, GREEN, GREEN, GREEN]

    HP3_PROBABILITY = 0.20 # 10%の確率でHP 3 (超高耐久・超高得点)
    HP2_PROBABILITY = 0.30 # 20%の確率でHP 2 (高耐久・高得点)
    
    for y in range(4): # 4行
        for x in range(10): # 10列
            
            # ランダムにHPとスコアを決定
            hp = 1
            score_value = 10 # 基本スコア
            
            rand_val = random.random()

            if rand_val < HP3_PROBABILITY:
                hp = 3
                score_value = 50 # HP 3 のスコア
            elif rand_val < HP3_PROBABILITY + HP2_PROBABILITY:
                hp = 2
                score_value = 30 # HP 2 のスコア
            # HP 1 は残りの確率 (70%)
            else:
                hp = 1
                score_value = 10 # HP 1 のスコア           
            # 行ごとに基本色を変える 
            color = block_colors[y % len(block_colors)]
                
            block = Block(
                x * (BLOCK_WIDTH + 8) + 20, # <--- 隙間を広げ、配置を見やすく調整
                y * (BLOCK_HEIGHT + 5) + 30, 
                color,
                hp=hp,             
                score_value=score_value
            )
            blocks.append(block)

    score = 0
    game_over = False
    game_clear = False

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
            hit_score = ball.update(paddle, blocks) # <--- 戻り値でスコアを取得
            if hit_score > 0: # ブロックを破壊した場合
                score += hit_score # スコア加算
            # ゲームオーバー判定
            if ball.is_out_of_bounds():
                game_over = True
            
            # ゲームクリア判定
            if not blocks: # ブロックがなくなったら
                game_clear = True

        # 描画処理
        screen.fill(BLACK) # 背景を黒で塗りつぶし
        paddle.draw(screen)
        ball.draw(screen)
        for block in blocks:
            block.draw(screen)

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