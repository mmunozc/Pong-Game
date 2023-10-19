#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <pthread.h>

#define PORT 8080
#define MAX_CLIENTS 100

void writeToLog(const char *message) {
    // Obtener la hora actual
    time_t rawtime;
    struct tm *timeinfo;
    time(&rawtime);
    timeinfo = localtime(&rawtime);

    // Abrir el archivo de registro en modo "agregar" (append)
    FILE *logFile = fopen("LogFile.txt", "a");
    if (logFile == NULL) {
        perror("Error al abrir el archivo de registro");
        exit(1); // Otra gestión de errores podría ser más apropiada
    }

    // Escribir la hora y el mensaje en el archivo de registro
    fprintf(logFile, "[%s] %s\n", asctime(timeinfo), message);

    // Cerrar el archivo de registro
    fclose(logFile);
}

typedef struct {
    int client_socket;
    char name[50];
    int paired; // 0 si no está emparejado, 1 si está emparejado
    int partner_index; // Índice del compañero en el arreglo clients
} ClientInfo;

typedef struct {
    ClientInfo *clients;
    int client_count;
    int client_index;
} ThreadData;

void *handle_client(void *data) {
    ThreadData *thread_data = (ThreadData *)data;
    ClientInfo *clients = thread_data->clients;
    int client_index = thread_data->client_index;
    char buffer[1024];

    while (1) {
        int bytes_received = recv(clients[client_index].client_socket, buffer, sizeof(buffer), 0);
        if (bytes_received <= 0) {
            close(clients[client_index].client_socket);
            clients[client_index].client_socket = -1;
            clients[client_index].paired = 0;
            printf("Cliente %s se desconectó.\n", clients[client_index].name);

            ///
            char log_message[256];
            snprintf(log_message, sizeof(log_message), "Cliente %s se desconectó.", clients[client_index].name);
            writeToLog(log_message);

            pthread_exit(NULL);
        }
        buffer[bytes_received] = '\0';
        
        // Envía el mensaje al compañero emparejado
        if (clients[client_index].paired) {
            int partner_index = clients[client_index].partner_index;
            send(clients[partner_index].client_socket, buffer, bytes_received, 0);
        }
    }
}

int main() {
    int server_socket, new_socket;
    struct sockaddr_in server_addr, new_addr;
    socklen_t addr_size;
    fd_set readfds;
    ClientInfo clients[MAX_CLIENTS] = {0};
    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    
    if (server_socket < 0) {
        perror("Error al crear el socket");
        exit(1);
    }
    
    printf("Servidor creado.\n");
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = INADDR_ANY;
    
    ///
    char log_message[256];
    snprintf(log_message, sizeof(log_message), "Servidor creado.\n");
    writeToLog(log_message);
    
    if (bind(server_socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Error en el binding");

        ///
        char log_message[256];
        snprintf(log_message, sizeof(log_message), "Error en el binding");
        writeToLog(log_message);

        exit(1);
    }
    
    if (listen(server_socket, MAX_CLIENTS) == 0) {
        printf("Escuchando...\n");

        ///
        char log_message[256];
        snprintf(log_message, sizeof(log_message), "Error en el binding");
        writeToLog(log_message);
        
    } else {
        printf("Error en la escucha.\n");

        ///
        char log_message[256];
        snprintf(log_message, sizeof(log_message), "Error en el binding");
        writeToLog(log_message);

        exit(1);
    }
    
    addr_size = sizeof(new_addr);
    
    while (1) {
        FD_ZERO(&readfds);
        FD_SET(server_socket, &readfds);
        int max_fd = server_socket;

        for (int i = 0; i < MAX_CLIENTS; i++) {
            int client_socket = clients[i].client_socket;
            if (client_socket > 0) {
                FD_SET(client_socket, &readfds);
                if (client_socket > max_fd) {
                    max_fd = client_socket;
                }
            }
        }


        if (FD_ISSET(server_socket, &readfds)) {
            new_socket = accept(server_socket, (struct sockaddr *)&new_addr, &addr_size);
           
            for (int i = 0; i < MAX_CLIENTS; i++) {

                if (clients[i].client_socket == 0) {
                    char aux[5];
                    clients[i].client_socket = new_socket;
                    printf("Nueva conexión, cliente (%d)\n", new_socket);
                    recv(new_socket, clients[i].name, sizeof(clients[i].name), 0);
                    sprintf(aux, "%d", new_socket);
                    send(clients[i].client_socket, aux, sizeof(new_socket), 0);
                    printf("Cliente %s\n", clients[i].name);
                    // Emparejar a los clientes y permitir que se comuniquen
                    for (int j = 0; j < MAX_CLIENTS; j++) {
                        if (clients[j].client_socket > 0 && !clients[j].paired && i != j) {
                            clients[i].paired = 1;
                            clients[j].paired = 1;
                            clients[i].partner_index = j;
                            clients[j].partner_index = i;
                            printf("Emparejando a %s y %s\n", clients[i].name, clients[j].name);

                            ///
                            char log_message[256];
                            snprintf(log_message, sizeof(log_message), "Empieza el juego entre %s y %s", clients[i].name, clients[j].name);
                            writeToLog(log_message);

                            char game_ready_message[] = "GAME_READY";

                            // Envía el mensaje "GAME_READY" al primer cliente emparejado
                            send(clients[j].client_socket, game_ready_message, strlen(game_ready_message), 0);

                            printf("Jugador 1 %s\n", clients[i].name);
                            printf("Jugador 2 %s\n", clients[j].name);

                            ///
                            snprintf(log_message, sizeof(log_message), "Jugador 1 %s se conectó", clients[i].name);
                            writeToLog(log_message);

                            ///
                            snprintf(log_message, sizeof(log_message), "Jugador 2 %s se conectó", clients[j].name);
                            writeToLog(log_message);

                            
                            // Crear hilos para manejar la comunicación entre las parejas emparejadas
                            ThreadData thread_data1;
                            thread_data1.clients = clients;
                            thread_data1.client_index = i;

                            ThreadData thread_data2;
                            thread_data2.clients = clients;
                            thread_data2.client_index = j;

                            pthread_t thread1, thread2;
                            pthread_create(&thread1, NULL, handle_client, &thread_data1);
                            pthread_create(&thread2, NULL, handle_client, &thread_data2);
                        }
                    }
                    break;
                }
            }

        }
    }
    close(server_socket);

    return 0;
}
