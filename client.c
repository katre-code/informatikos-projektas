#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>

#define SOCKET_FILE "./game.sock"
#define BUFFER_SIZE 4096

void error_exit(const char* message) {
    perror(message);
    exit(EXIT_FAILURE);
}

int main() {
    int socket_fd;
    struct sockaddr_un server_address;
    char buffer[BUFFER_SIZE];

    // Try to create a Unix socket
    if ((socket_fd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0)
        error_exit("Failed to create socket...");

    // Set server address
    memset(&server_address, 0, sizeof(server_address));
    memset(buffer, 0, BUFFER_SIZE);

    server_address.sun_family = AF_UNIX;
    strncpy(server_address.sun_path, SOCKET_FILE,
        sizeof(server_address.sun_path) - 1);

    // Try to connect to the server
    if (connect(socket_fd, (struct sockaddr*)&server_address,
        sizeof(server_address)) < 0)
        error_exit("Failed to connect to server...");

    printf("Connected to server.\n");

    // Receive the first message from the server
    memset(buffer, 0, BUFFER_SIZE);
    if (recv(socket_fd, buffer, BUFFER_SIZE, 0) > 0)
        printf("%s", buffer);

    // Communication loop
    while (1) {
        printf(" Response: ");
        fgets(buffer, BUFFER_SIZE, stdin);

        // Remove newline
        buffer[strcspn(buffer, "\n")] = '\0';

        // If user enters "exit"
        if (strcmp(buffer, "exit") == 0)
            break;

        send(socket_fd, buffer, strlen(buffer), 0);
        memset(buffer, 0, BUFFER_SIZE);

        if (recv(socket_fd, buffer, BUFFER_SIZE, 0) > 0)
            printf("Server: %s", buffer);

        // If the server signals end of game
        if (strncmp("END", buffer, 3) == 0)
            break;
    }

    // Close the socket
    close(socket_fd);
    printf("Session ended.\n");
    return 0;
}
