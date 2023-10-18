import pygame
import random
import socket
import threading
import time



WIDTH, HEIGHT = 1200, 600
ballVel = 0.1
new_paddle_b_y = HEIGHT // 2 - 40
game_ready = False



def receive_messages(client_socket):
    global new_paddle_b_y
    global bola_x
    global bola_y
    global punt_a
    global punt_b
    global game_ready
    while True:
        data = client_socket.recv(1024).decode()
        # Analizar el mensaje para obtener la posición de la paleta derecha
        if data.startswith("SUBIO ") or data.startswith("BAJO "):
            try:
                action, value = data.split()
                if action == "SUBIO":
                    new_paddle_b_y = float(value)
                elif action == "BAJO":
                    new_paddle_b_y = float(value)
            except ValueError:
                print("Error al analizar la posición recibida.")
        elif data.startswith("BOLA ") and int(aux) % 2 != 0:
            try:
                action, posicionX, posicionY = data.split()
                bola_x = (WIDTH - 20) - float(posicionX)
                bola_y = float(posicionY)
            except ValueError:
                print("Error al procesar la información de la bola.")
        elif data.startswith("PUNTAJE ") and int(aux) % 2 != 0:
            try:
                action, puntA, puntB = data.split()
                punt_a = int(puntA)
                punt_b = int(puntB)
            except ValueError:
                print("Error al procesar la información del puntaje.")
        elif data.startswith("GAME_READY") and int(aux) % 2 == 0:
            try:
                print("ENTRO")
                game_ready = True
            except ValueError:
                print("Error")


def get_player_name(screen):
    player_name = ""
    font = pygame.font.Font(None, 36)
    text = ""
    input_active = True

    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

        screen.fill((30, 30, 30))
        if input_active:
            prompt = font.render("Ingrese su nombre:", True, (255, 255, 255))
            text_surface = font.render(text, True, (255, 255, 255))
            screen.blit(prompt, (450, 300))
            screen.blit(text_surface, (450, 350))
            pygame.display.flip()

        

    return text

def main():
    global new_paddle_b_y
    global prueba
    global bola_x
    global bola_y
    global punt_a
    global punt_b
    global aux
    global game_ready
    
    host = "127.0.0.1"
    port = 8080
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    # Inicializar Pygame
    pygame.init()
    pygame.font.init()
    # Configuración de la pantalla
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pong")

    player_name = get_player_name(screen)
    client_socket.send(player_name.encode())

    aux = client_socket.recv(1).decode()
    print(aux)

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    if int(aux) % 2 == 0:
        while not game_ready:
            print("Esperando a que el otro jugador se una...")
            pygame.display.update()
    else:
        punt_a = 0
        punt_b = 0
        bola_x = 0
        bola_y = 0
        print("JUGADOR 2")


    # Colores
    WHITE = (255, 255, 255)

    # Inicialización de las posiciones y velocidades de las paletas y la pelota
    ball_x = WIDTH - 10 // 2
    ball_y = HEIGHT - 10 // 2
    ball_speed_x = ballVel #* random.choice((1, -1))
    ball_speed_y = ballVel #* random.choice((1, -1))

    paddle_a_x = 10
    paddle_a_y = HEIGHT // 2 - 40 
    paddle_b_x = WIDTH - 20
    if 0 <= new_paddle_b_y <= HEIGHT - 80:
        paddle_b_y = new_paddle_b_y
    paddle_speed = .3

    # Puntuación
    if int(aux) % 2 == 0:
        score_a = -1
    else:
        score_a = 0

    score_b = 0

    font = pygame.font.Font(None, 36)

    # Bucle principal del juego
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()

        pos = ''
        if keys[pygame.K_w] and paddle_a_y > 0:
            paddle_a_y -= paddle_speed
            pos = "SUBIO " + str(paddle_a_y)
            client_socket.send(pos.encode())
    

        if keys[pygame.K_s] and paddle_a_y < HEIGHT - 80:
            paddle_a_y += paddle_speed
            pos = "BAJO " + str(paddle_a_y)
            client_socket.send(pos.encode())

        # Actualizar la posición de la paleta derecha con la posición global
        paddle_b_y = new_paddle_b_y

        if int(aux) % 2 == 0:
            puntaje = "PUNTAJE " + str(score_a) + " " + str(score_b)
            client_socket.send(puntaje.encode())
        else:
            score_a = punt_a
            score_b = punt_b

        # Actualizar la posición de la pelota
        if int(aux) % 2 == 0:
            ball_x += ball_speed_x
            ball_y += ball_speed_y   

            posBall = "BOLA " + str(ball_x) + " " + str(ball_y)
            #print(posBall)
            client_socket.send(posBall.encode())
        else:
            ball_x = bola_x
            ball_y = bola_x

        # Colisiones de la pelota con las paredes
        if ball_y <= 0 or ball_y >= HEIGHT - 20:
            ball_speed_y *= -1

        # Colisiones de la pelota con las paletas
        if (
            ball_x <= paddle_a_x + 10
            and paddle_a_y < ball_y < paddle_a_y + 80
        ) or (
            ball_x >= paddle_b_x - 10
            and paddle_b_y < ball_y < paddle_b_y + 80
        ):
            ball_speed_x *= -1

        # Punto para el jugador A
        if ball_x >= WIDTH - 20:
            score_a += 1

            ball_x = WIDTH // 2
            ball_y = HEIGHT // 2
            ball_speed_x = ballVel * random.choice((1, -1))
            ball_speed_y = ballVel * random.choice((1, -1))

        # Punto para el jugador B
        if ball_x <= 0:
            score_b += 1

            ball_x = WIDTH // 2
            ball_y = HEIGHT // 2
            ball_speed_x = ballVel * random.choice((1, -1))
            ball_speed_y = ballVel * random.choice((1, -1))

        # Verificar si uno de los jugadores llegó a 7 puntos para terminar el juego
        if score_a == 100 or score_b == 100:
            running = False

        # Limpiar la pantalla
        screen.fill((0, 0, 0))

        # Dibujar las paletas y la pelota
        pygame.draw.rect(screen, WHITE, (paddle_a_x, paddle_a_y, 10, 80))
        pygame.draw.rect(screen, WHITE, (paddle_b_x, paddle_b_y, 10, 80))
        pygame.draw.ellipse(screen, WHITE, (ball_x, ball_y, 20, 20))

        # Mostrar la puntuación en la pantalla
        score_display = font.render(f"{score_a}  {score_b}", True, WHITE)
        screen.blit(score_display, (WIDTH // 2 - 19, 10))

        # Linea del centro
        pygame.draw.line(screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 5)

        # Actualizar la pantalla
        pygame.display.update()

    # Salir de Pygame
    pygame.quit()

if __name__ == "__main__":
    main()