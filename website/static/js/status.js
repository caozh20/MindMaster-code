function updateUserRoomStatus() {
    $.ajax({
        url: '/admin/status',
        type: 'GET',
        dataType: 'json',
        success: function(data) {

            const userUuid = document.cookie.match(/sid=([^;]+)/)[1];
            
            const userStatus = data.users[userUuid];
            const roomStatus = data.rooms[userStatus.roomId];
            
            // Extract partner UUID from roomStatus
            let partnerUuid = null;
            if (roomStatus && roomStatus.users) {
                partnerUuid = roomStatus.users.find(user => {
                    const [uuid, email] = user.split(':');
                    return uuid !== userUuid;
                });
                if (partnerUuid) {
                    partnerUuid = partnerUuid.split(':')[0];
                }
            }
            
            $('#user-email').text(userStatus.email);
            $('#user-status-value').text(userStatus.status);

            $('#room-id').text(userStatus.roomId);
            $('#room-status-value').text(roomStatus ? roomStatus.status : 'N/A');

            // Update status colors
            $('#user-status-value').removeClass().addClass(getStatusClass(userStatus.status));
            $('#room-status-value').removeClass().addClass(getStatusClass(roomStatus ? roomStatus.status : ''));

            $('#partner-email').text('******');      
            let partnerStatusDesc = 'pending';
            if (partnerUuid) {
                const partnerStatus = data.users[partnerUuid];
                $('#partner-status-value').text(partnerStatus.status);
                partnerStatusDesc = partnerStatus.status;
                $('#other-action').text(userStatus.other_last_action);
                $('#last-action-text').html(userStatus.other_last_action);
                $('#partner-status-value').removeClass().addClass(getStatusClass(partnerStatus.status));
            } else {
                $('#partner-status-value').text('pending');
                partnerStatusDesc = 'pending';
                $('#partner-status-value').removeClass().addClass(getStatusClass('pending'));
            }

            // Update game status message
            updateGameStatusMessage(partnerStatusDesc);
        },
        error: function(xhr, status, error) {
            console.error('Error fetching status:', error);
        }
    });
}

function updateGameStatusMessage(partnerStatusDesc) {
    const statusElement = $('#game-status-message');
    let message = '';
    let color = '';

    switch(partnerStatusDesc) {
        case 'pending':
            message = 'Waiting for another player to join...';
            color = '#007bff'; 
            break;
        case 'playing':
            message = 'Game in progress';
            color = '#28a745'; 
            break;
        case 'quit':
            message = 'Other player unexpectedly left. Please log in again.';
            color = '#dc3545'; 
            break;
        default:
            message = '';
            color = '';
    }

    statusElement.text(message);
    statusElement.css('color', color);
}

function getStatusClass(status) {
    switch (status.toLowerCase()) {
        case 'busy':
            return 'status-busy';
        case 'available':
            return 'status-available';
        case 'unavailable':
            return 'status-unavailable';
        case 'playing':
            return 'status-playing';
        case 'waiting':
            return 'status-waiting';
        case 'finished':
            return 'status-finished';
        case 'quit':
            return 'status-quit';
        case 'pending':
            return 'status-pending';
        default:
            return '';
    }
}

// Update status every 1 seconds
setInterval(updateUserRoomStatus, 1000);

// Initial update
updateUserRoomStatus();