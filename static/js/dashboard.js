(function () {
    'use strict';

    const statusLabels = {
        todo: 'To do',
        in_progress: 'In progress',
        done: 'Done'
    };
    const priorityLabels = {
        low: 'Low',
        medium: 'Medium',
        high: 'High'
    };

    let tasks = [];
    let modal;

    const els = {};

    document.addEventListener('DOMContentLoaded', function () {
        els.tableBody = document.getElementById('taskTableBody');
        els.emptyState = document.getElementById('emptyState');
        els.search = document.getElementById('searchInput');
        els.statusFilter = document.getElementById('statusFilter');
        els.priorityFilter = document.getElementById('priorityFilter');
        els.sort = document.getElementById('sortSelect');
        els.order = document.getElementById('orderSelect');
        els.stats = document.getElementById('taskStats');
        els.form = document.getElementById('taskForm');
        els.formErrors = document.getElementById('formErrors');
        els.modalTitle = document.getElementById('taskModalTitle');
        els.taskId = document.getElementById('taskId');
        els.title = document.getElementById('title');
        els.description = document.getElementById('description');
        els.status = document.getElementById('status');
        els.priority = document.getElementById('priority');
        els.dueDate = document.getElementById('dueDate');
        modal = new bootstrap.Modal(document.getElementById('taskModal'));

        document.getElementById('newTaskBtn').addEventListener('click', openCreateModal);
        els.form.addEventListener('submit', saveTask);
        els.tableBody.addEventListener('click', handleTableClick);
        [els.statusFilter, els.priorityFilter, els.sort, els.order].forEach(function (el) {
            el.addEventListener('change', loadTasks);
        });
        els.search.addEventListener('input', debounce(loadTasks, 250));

        loadTasks();
    });

    async function loadTasks() {
        const params = new URLSearchParams();
        if (els.search.value.trim()) params.set('search', els.search.value.trim());
        if (els.statusFilter.value) params.set('status', els.statusFilter.value);
        if (els.priorityFilter.value) params.set('priority', els.priorityFilter.value);
        params.set('sort', els.sort.value);
        params.set('order', els.order.value);

        try {
            const data = await window.TaskNest.apiFetch('/api/tasks?' + params.toString());
            tasks = data.tasks || [];
            renderTasks();
            renderStats();
        } catch (error) {
            showTableError(error.message);
        }
    }

    function renderTasks() {
        els.tableBody.textContent = '';
        els.emptyState.classList.toggle('d-none', tasks.length > 0);
        tasks.forEach(function (task) {
            const tr = document.createElement('tr');

            const taskCell = document.createElement('td');
            const title = document.createElement('div');
            title.className = 'task-title';
            title.textContent = task.title;
            const description = document.createElement('div');
            description.className = 'task-description text-truncate';
            description.textContent = task.description || 'No description';
            taskCell.append(title, description);

            const statusCell = document.createElement('td');
            statusCell.append(makeBadge(statusLabels[task.status] || task.status));

            const priorityCell = document.createElement('td');
            priorityCell.append(makeBadge(priorityLabels[task.priority] || task.priority));

            const dueCell = document.createElement('td');
            dueCell.textContent = task.due_date || '—';

            const ownerCell = document.createElement('td');
            ownerCell.textContent = task.owner_name || '—';

            const actionsCell = document.createElement('td');
            actionsCell.className = 'text-end btn-icon-group';
            const editButton = document.createElement('button');
            editButton.type = 'button';
            editButton.className = 'btn btn-outline-primary btn-sm me-2';
            editButton.dataset.action = 'edit';
            editButton.dataset.id = task.id;
            editButton.textContent = 'Edit';
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'btn btn-outline-danger btn-sm';
            deleteButton.dataset.action = 'delete';
            deleteButton.dataset.id = task.id;
            deleteButton.textContent = 'Delete';
            actionsCell.append(editButton, deleteButton);

            tr.append(taskCell, statusCell, priorityCell, dueCell, ownerCell, actionsCell);
            els.tableBody.append(tr);
        });
    }

    function renderStats() {
        const total = tasks.length;
        const open = tasks.filter(function (task) { return task.status !== 'done'; }).length;
        const high = tasks.filter(function (task) { return task.priority === 'high'; }).length;
        els.stats.textContent = '';
        [
            ['Total', total],
            ['Open', open],
            ['High', high]
        ].forEach(function (item) {
            const card = document.createElement('div');
            card.className = 'stat-card';
            const value = document.createElement('strong');
            value.textContent = item[1];
            const label = document.createElement('span');
            label.textContent = item[0];
            card.append(value, label);
            els.stats.append(card);
        });
    }

    function openCreateModal() {
        els.form.reset();
        els.form.classList.remove('was-validated');
        hideFormErrors();
        els.taskId.value = '';
        els.modalTitle.textContent = 'New task';
        els.status.value = 'todo';
        els.priority.value = 'medium';
        modal.show();
    }

    function openEditModal(task) {
        els.form.reset();
        els.form.classList.remove('was-validated');
        hideFormErrors();
        els.taskId.value = task.id;
        els.title.value = task.title;
        els.description.value = task.description || '';
        els.status.value = task.status;
        els.priority.value = task.priority;
        els.dueDate.value = task.due_date || '';
        els.modalTitle.textContent = 'Edit task';
        modal.show();
    }

    async function saveTask(event) {
        event.preventDefault();
        els.form.classList.add('was-validated');
        hideFormErrors();
        if (!els.form.checkValidity()) return;

        const payload = {
            title: els.title.value.trim(),
            description: els.description.value.trim(),
            status: els.status.value,
            priority: els.priority.value,
            due_date: els.dueDate.value
        };
        const id = els.taskId.value;
        const url = id ? '/api/tasks/' + encodeURIComponent(id) : '/api/tasks';
        const method = id ? 'PUT' : 'POST';

        try {
            await window.TaskNest.apiFetch(url, { method: method, body: JSON.stringify(payload) });
            modal.hide();
            await loadTasks();
        } catch (error) {
            showFormErrors(error.message);
        }
    }

    async function handleTableClick(event) {
        const button = event.target.closest('button[data-action]');
        if (!button) return;
        const id = Number(button.dataset.id);
        const task = tasks.find(function (item) { return item.id === id; });
        if (!task) return;
        if (button.dataset.action === 'edit') {
            openEditModal(task);
        }
        if (button.dataset.action === 'delete') {
            const ok = window.confirm('Delete this task?');
            if (!ok) return;
            try {
                await window.TaskNest.apiFetch('/api/tasks/' + encodeURIComponent(id), { method: 'DELETE' });
                await loadTasks();
            } catch (error) {
                showTableError(error.message);
            }
        }
    }

    function makeBadge(text) {
        const badge = document.createElement('span');
        badge.className = 'badge rounded-pill badge-soft';
        badge.textContent = text;
        return badge;
    }

    function showFormErrors(message) {
        els.formErrors.textContent = message;
        els.formErrors.classList.remove('d-none');
    }

    function hideFormErrors() {
        els.formErrors.textContent = '';
        els.formErrors.classList.add('d-none');
    }

    function showTableError(message) {
        els.tableBody.textContent = '';
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.colSpan = 6;
        td.className = 'text-danger py-4';
        td.textContent = message;
        tr.append(td);
        els.tableBody.append(tr);
    }

    function debounce(fn, delay) {
        let timer;
        return function () {
            window.clearTimeout(timer);
            timer = window.setTimeout(fn, delay);
        };
    }
})();
