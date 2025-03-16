// theme/js/calendar.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("FullCalendar script is running...");

    const calendarEl = document.getElementById('calendar');
    
    if (!calendarEl) {
        console.error("L'élément #calendar est introuvable !");
        return;
    }

    // Vérifier si FullCalendar est bien chargé
    if (typeof FullCalendar === "undefined") {
        console.error("FullCalendar n'est pas chargé !");
        return;
    }

    console.log("FullCalendar est chargé avec succès !");

    function getRandomColor() {
        return `#${Math.floor(Math.random()*16777215).toString(16)}`;
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: [
            {% for schedule in work_schedules %}
                {
                    title: "{{ schedule.employee.name }}",
                    start: "{{ schedule.start_time|date:'Y-m-d' }}T{{ schedule.start_time|time:'H:i:s' }}",
                    end: "{{ schedule.end_time|date:'Y-m-d' }}T{{ schedule.end_time|time:'H:i:s' }}",
                    color: getRandomColor()
                }{% if not forloop.last %},{% endif %}
            {% endfor %}
        ],
        eventClick: function(info) {
            alert(`Employé: ${info.event.title}\nHeure: ${info.event.start.toLocaleTimeString()} - ${info.event.end.toLocaleTimeString()}`);
        }
    });

    calendar.render();
});