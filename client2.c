"""cia visas client kodas tsg is chat gpt, naudojau sita kai testavau serveri, tai nezinau galim gal sita naudot"""

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>

#define SOCKET_PATH "./game.sock"
#define BUFFER_SIZE 1024

int main() {
    int sock;
    struct sockaddr_un server_addr;
    char buffer[BUFFER_SIZE];

    // Create socket
    if ((sock = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, SOCKET_PATH, sizeof(server_addr.sun_path) - 1);

    // Connect to server
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        perror("connect");
        close(sock);
        exit(EXIT_FAILURE);
    }

    while (1) {
        memset(buffer, 0, BUFFER_SIZE);

        // Read message from server
        int bytes_received = read(sock, buffer, BUFFER_SIZE - 1);
        if (bytes_received <= 0) {
            printf("Server disconnected.\n");
            break;
        }

        printf("%s", buffer); // print server message

        // If server asks to end
        if (strstr(buffer, "END") != NULL) {
            break;
        }

        // Get user input
        char input[BUFFER_SIZE];
        if (fgets(input, sizeof(input), stdin) != NULL) {
            // Remove newline
            input[strcspn(input, "\n")] = '\0';
            write(sock, input, strlen(input));
        }
    }

    close(sock);
    return 0;
}

