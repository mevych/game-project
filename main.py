import sys
import pygame
from constants import *
from sound import sfx
from effects import camera_shake, floating_text
from game import Game


def main():
    pygame.mixer.pre_init(22050, -16, 2, 512)
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Avengers project")
    clock = pygame.time.Clock()

    game = Game()

    current_music_state = None

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.state == "MENU":
                    game.handle_menu_clicks()
                elif game.state == "DIFFICULTY_SELECT":
                    game.handle_difficulty_clicks()
                elif game.state == "HANGAR":
                    game.handle_hangar_clicks()
                elif game.state == "CASINO":
                    game.handle_casino_clicks()
                elif game.state == "PLAYING" and game.paused:
                    game.handle_pause_clicks()
                elif game.state == "INSTRUCTIONS":
                    mx, my = pygame.mouse.get_pos()
                    if pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT - 110, 320, 48).collidepoint(mx, my):
                        sfx.play('click')
                        game.state = "MENU"
                elif game.state == "LEADERBOARD":
                    mx, my = pygame.mouse.get_pos()
                    if pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT - 130, 320, 48).collidepoint(mx, my):
                        sfx.play('click')
                        game.state = "MENU"
                elif game.state == "GAMEOVER":
                    mx, my = pygame.mouse.get_pos()
                    if pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 40, 320, 48).collidepoint(mx, my):
                        sfx.play('click')
                        game.start_new_game()
                    elif pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 110, 320, 48).collidepoint(mx, my):
                        sfx.play('click')
                        game.state = "MENU"
                elif game.state == "VICTORY":
                    mx, my = pygame.mouse.get_pos()
                    if pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 80, 320, 48).collidepoint(mx, my):
                        sfx.play('click')
                        game.enable_freeplay_mode()
                    elif pygame.Rect(SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 + 150, 320, 48).collidepoint(mx, my):
                        sfx.play('click')
                        game.state = "MENU"

            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_m, 1084]:
                    sfx.toggle_music()
                    state_str = "ON" if sfx.music_enabled else "OFF"
                    floating_text.spawn(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, f"MUSIC: {state_str}", COLOR_CYAN, 24)

                elif event.key == pygame.K_ESCAPE:
                    if game.state == "PLAYING":
                        game.paused = not game.paused
                elif event.key == pygame.K_SPACE:
                    if game.state == "STAGE_CLEAR":
                        game.handle_stage_clear_keys()

        if game.state == "PLAYING" and not game.paused:
            keys = pygame.key.get_pressed()
            game.player.move(keys)
            if keys[pygame.K_SPACE]:
                game.player.shoot(game.player_lasers)

        game.update()

        if sfx.music_enabled:
            if game.state == "PLAYING" and game.boss and game.boss.name == "BIG BOSS":
                if current_music_state != "shagohod":
                    sfx.play_music("sounds/final boss theme.mp3", volume=0.45)
                    current_music_state = "shagohod"
            elif game.state in ["MENU", "HANGAR"]:
                if current_music_state != "menu":
                    sfx.play_music("sounds/menu.mp3", volume=0.3)
                    current_music_state = "menu"
            elif game.state in ["PLAYING", "BOSS_FIGHT"]:
                if current_music_state != "game":
                    sfx.play_music("sounds/game.mp3", volume=0.3)
                    current_music_state = "game"
            elif game.state in ["GAME_OVER", "VICTORY"]:
                if current_music_state != "stopped":
                    sfx.stop_music()
                    current_music_state = "stopped"
        else:
            if current_music_state != "stopped":
                sfx.stop_music()
                current_music_state = "stopped"

        game.draw(screen)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()