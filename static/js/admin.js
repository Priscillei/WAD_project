(function () {
    'use strict';

    let currentUserId = null;
    const tbody = document.getElementById('usersTableBody');
    const emptyState = document.getElementById('usersEmptyState');

    document.addEventListener('DOMContentLoaded', function () {
        tbody.addEventListener('change', handleRoleChange);
        tbody.addEventListener('click', handleDeleteClick);
        loadUsers();
    });

    async function loadUsers() {
        try {
            const me = await window.TaskNest.apiFetch('/api/me');
            currentUserId = me.user.id;
            const data = await window.TaskNest.apiFetch('/api/users');
            renderUsers(data.users || []);
        } catch (error) {
            renderError(error.message);
        }
    }

    function renderUsers(users) {
        tbody.textContent = '';
        emptyState.classList.toggle('d-none', users.length > 0);
        users.forEach(function (user) {
            const tr = document.createElement('tr');

            const nameCell = document.createElement('td');
            const name = document.createElement('strong');
            name.textContent = user.name;
            nameCell.append(name);

            const emailCell = document.createElement('td');
            emailCell.textContent = user.email;

            const roleCell = document.createElement('td');
            const roleSelect = document.createElement('select');
            roleSelect.className = 'form-select form-select-sm';
            roleSelect.dataset.id = user.id;
            ['user', 'admin'].forEach(function (role) {
                const option = document.createElement('option');
                option.value = role;
                option.textContent = role;
                option.selected = role === user.role;
                roleSelect.append(option);
            });
            roleCell.append(roleSelect);

            const tasksCell = document.createElement('td');
            tasksCell.textContent = user.task_count;

            const createdCell = document.createElement('td');
            createdCell.textContent = user.created_at;

            const actionsCell = document.createElement('td');
            actionsCell.className = 'text-end';
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'btn btn-outline-danger btn-sm';
            deleteButton.dataset.action = 'delete-user';
            deleteButton.dataset.id = user.id;
            deleteButton.textContent = user.id === currentUserId ? 'Current user' : 'Delete';
            deleteButton.disabled = user.id === currentUserId;
            actionsCell.append(deleteButton);

            tr.append(nameCell, emailCell, roleCell, tasksCell, createdCell, actionsCell);
            tbody.append(tr);
        });
    }

    async function handleRoleChange(event) {
        const select = event.target.closest('select[data-id]');
        if (!select) return;
        try {
            await window.TaskNest.apiFetch('/api/users/' + encodeURIComponent(select.dataset.id), {
                method: 'PATCH',
                body: JSON.stringify({ role: select.value })
            });
            await loadUsers();
        } catch (error) {
            window.alert(error.message);
            await loadUsers();
        }
    }

    async function handleDeleteClick(event) {
        const button = event.target.closest('button[data-action="delete-user"]');
        if (!button || button.disabled) return;
        const ok = window.confirm('Delete this user and all their tasks?');
        if (!ok) return;
        try {
            await window.TaskNest.apiFetch('/api/users/' + encodeURIComponent(button.dataset.id), { method: 'DELETE' });
            await loadUsers();
        } catch (error) {
            window.alert(error.message);
        }
    }

    function renderError(message) {
        tbody.textContent = '';
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 6;
        td.className = 'text-danger py-4';
        td.textContent = message;
        tr.append(td);
        tbody.append(tr);
    }
})();
