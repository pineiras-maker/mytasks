import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import uuid
import calendar

# Configure page
st.set_page_config(
    page_title="Task Calendar",
    page_icon="📅",
    layout="wide"
)

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = {}
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'daily'
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()
if 'selected_week_start' not in st.session_state:
    # Get Monday of current week
    today = datetime.now().date()
    days_since_monday = today.weekday()
    st.session_state.selected_week_start = today - timedelta(days=days_since_monday)

def save_tasks():
    """Save tasks to a JSON file"""
    try:
        with open('tasks.json', 'w') as f:
            json.dump(st.session_state.tasks, f, default=str)
    except Exception as e:
        st.error(f"Error saving tasks: {e}")

def load_tasks():
    """Load tasks from JSON file"""
    try:
        with open('tasks.json', 'r') as f:
            st.session_state.tasks = json.load(f)
    except FileNotFoundError:
        st.session_state.tasks = {}
    except Exception as e:
        st.error(f"Error loading tasks: {e}")

def add_task(date_str, title, priority, description=""):
    """Add a new task"""
    task_id = str(uuid.uuid4())
    if date_str not in st.session_state.tasks:
        st.session_state.tasks[date_str] = {}
    
    st.session_state.tasks[date_str][task_id] = {
        'title': title,
        'description': description,
        'priority': priority,
        'completed': False,
        'created_at': datetime.now().isoformat()
    }
    save_tasks()

def toggle_task_completion(date_str, task_id):
    """Toggle task completion status"""
    if date_str in st.session_state.tasks and task_id in st.session_state.tasks[date_str]:
        st.session_state.tasks[date_str][task_id]['completed'] = not st.session_state.tasks[date_str][task_id]['completed']
        save_tasks()

def delete_task(date_str, task_id):
    """Delete a task"""
    if date_str in st.session_state.tasks and task_id in st.session_state.tasks[date_str]:
        del st.session_state.tasks[date_str][task_id]
        if not st.session_state.tasks[date_str]:
            del st.session_state.tasks[date_str]
        save_tasks()

def move_incomplete_tasks():
    """Move incomplete tasks from previous days to today"""
    today = datetime.now().date()
    today_str = today.strftime('%Y-%m-%d')
    moved_count = 0
    
    dates_to_check = []
    for date_str in list(st.session_state.tasks.keys()):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            if date_obj < today:
                dates_to_check.append(date_str)
        except ValueError:
            continue
    
    for date_str in dates_to_check:
        if date_str in st.session_state.tasks:
            tasks_to_move = []
            for task_id, task in st.session_state.tasks[date_str].items():
                if not task['completed']:
                    tasks_to_move.append((task_id, task))
            
            for task_id, task in tasks_to_move:
                if today_str not in st.session_state.tasks:
                    st.session_state.tasks[today_str] = {}
                
                new_task_id = str(uuid.uuid4())
                st.session_state.tasks[today_str][new_task_id] = task.copy()
                st.session_state.tasks[today_str][new_task_id]['moved_from'] = date_str
                
                del st.session_state.tasks[date_str][task_id]
                moved_count += 1
            
            if not st.session_state.tasks[date_str]:
                del st.session_state.tasks[date_str]
    
    if moved_count > 0:
        save_tasks()
        st.success(f"Moved {moved_count} incomplete tasks to today!")

def get_sorted_tasks(date_str):
    """Get tasks for a date sorted by priority"""
    if date_str not in st.session_state.tasks:
        return []
    
    tasks = st.session_state.tasks[date_str]
    priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
    
    sorted_tasks = sorted(
        tasks.items(),
        key=lambda x: (x[1]['completed'], priority_order.get(x[1]['priority'], 4), x[1]['title'])
    )
    
    return sorted_tasks

def get_priority_color(priority):
    """Get color for priority display"""
    colors = {
        'High': '🔴',
        'Medium': '🟡', 
        'Low': '🟢'
    }
    return colors.get(priority, '⚪')

def create_calendar_widget():
    """Create a visual calendar widget"""
    st.subheader("📅 Calendar")
    
    # Month navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    current_date = st.session_state.selected_date
    current_month = current_date.month
    current_year = current_date.year
    
    with col1:
        if st.button("◀", key="prev_month"):
            if current_month == 1:
                new_date = current_date.replace(year=current_year-1, month=12)
            else:
                new_date = current_date.replace(month=current_month-1)
            st.session_state.selected_date = new_date
            st.rerun()
    
    with col2:
        st.write(f"**{calendar.month_name[current_month]} {current_year}**")
    
    with col3:
        if st.button("▶", key="next_month"):
            if current_month == 12:
                new_date = current_date.replace(year=current_year+1, month=1)
            else:
                new_date = current_date.replace(month=current_month+1)
            st.session_state.selected_date = new_date
            st.rerun()
    
    # Calendar grid
    cal = calendar.monthcalendar(current_year, current_month)
    
    # Days of week header
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    cols = st.columns(7)
    for i, day in enumerate(days):
        with cols[i]:
            st.markdown(f"**{day}**")
    
    # Calendar days
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.write("")
                else:
                    date_obj = datetime(current_year, current_month, day).date()
                    date_str = date_obj.strftime('%Y-%m-%d')
                    
                    # Check if date has tasks
                    task_count = len(st.session_state.tasks.get(date_str, {}))
                    completed_count = sum(1 for task in st.session_state.tasks.get(date_str, {}).values() if task['completed'])
                    
                    # Styling for today and selected date
                    is_today = date_obj == datetime.now().date()
                    is_selected = date_obj == st.session_state.selected_date
                    
                    button_label = f"{day}"
                    if task_count > 0:
                        button_label += f"\n({completed_count}/{task_count})"
                    
                    button_type = "primary" if is_selected else "secondary"
                    if is_today and not is_selected:
                        button_label += " 📍"
                    
                    if st.button(button_label, key=f"cal_{date_str}", type=button_type, use_container_width=True):
                        st.session_state.selected_date = date_obj
                        # Update week start if in weekly mode
                        if st.session_state.view_mode == 'weekly':
                            days_since_monday = date_obj.weekday()
                            st.session_state.selected_week_start = date_obj - timedelta(days=days_since_monday)
                        st.rerun()

def display_daily_tasks():
    """Display tasks for selected day"""
    date_str = st.session_state.selected_date.strftime('%Y-%m-%d')
    st.subheader(f"Tasks for {st.session_state.selected_date.strftime('%A, %B %d, %Y')}")
    
    tasks = get_sorted_tasks(date_str)
    
    if not tasks:
        st.info("No tasks for this date. Add a task using the sidebar!")
    else:
        for task_id, task in tasks:
            with st.container():
                col_check, col_content, col_actions = st.columns([0.5, 4, 0.5])
                
                with col_check:
                    if st.checkbox("", value=task['completed'], key=f"check_{task_id}"):
                        if not task['completed']:
                            toggle_task_completion(date_str, task_id)
                            st.rerun()
                    elif task['completed']:
                        toggle_task_completion(date_str, task_id)
                        st.rerun()
                
                with col_content:
                    priority_icon = get_priority_color(task['priority'])
                    title_style = "text-decoration: line-through; opacity: 0.6;" if task['completed'] else ""
                    
                    st.markdown(f"""
                    <div style="{title_style}">
                        {priority_icon} <strong>{task['title']}</strong>
                        <br><small>Priority: {task['priority']}</small>
                        {f"<br><em>{task['description']}</em>" if task['description'] else ""}
                        {'<br><small>📁 Moved from previous day</small>' if task.get('moved_from') else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_actions:
                    if st.button("🗑️", key=f"del_{task_id}", help="Delete task"):
                        delete_task(date_str, task_id)
                        st.rerun()
                
                st.divider()

def display_weekly_tasks():
    """Display tasks for selected week"""
    week_start = st.session_state.selected_week_start
    week_end = week_start + timedelta(days=6)
    
    st.subheader(f"Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    
    # Week navigation
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("◀ Previous Week", key="prev_week"):
            st.session_state.selected_week_start -= timedelta(days=7)
            st.rerun()
    with col3:
        if st.button("Next Week ▶", key="next_week"):
            st.session_state.selected_week_start += timedelta(days=7)
            st.rerun()
    
    # Display each day of the week
    for i in range(7):
        current_day = week_start + timedelta(days=i)
        date_str = current_day.strftime('%Y-%m-%d')
        day_name = current_day.strftime('%A, %B %d')
        
        # Day header
        is_today = current_day == datetime.now().date()
        header_text = f"**{day_name}**"
        if is_today:
            header_text += " 📍"
        
        st.markdown(header_text)
        
        # Tasks for this day
        tasks = get_sorted_tasks(date_str)
        
        if not tasks:
            st.markdown("*No tasks*")
        else:
            # Create columns for tasks
            for task_id, task in tasks[:5]:  # Show max 5 tasks per day in weekly view
                col_check, col_content, col_actions = st.columns([0.3, 4, 0.3])
                
                with col_check:
                    if st.checkbox("", value=task['completed'], key=f"week_check_{task_id}"):
                        if not task['completed']:
                            toggle_task_completion(date_str, task_id)
                            st.rerun()
                    elif task['completed']:
                        toggle_task_completion(date_str, task_id)
                        st.rerun()
                
                with col_content:
                    priority_icon = get_priority_color(task['priority'])
                    title_style = "text-decoration: line-through; opacity: 0.6;" if task['completed'] else ""
                    st.markdown(f'<span style="{title_style}">{priority_icon} {task["title"]}</span>', unsafe_allow_html=True)
                
                with col_actions:
                    if st.button("🗑️", key=f"week_del_{task_id}", help="Delete task"):
                        delete_task(date_str, task_id)
                        st.rerun()
            
            # Show "and X more" if there are more tasks
            if len(tasks) > 5:
                st.markdown(f"*... and {len(tasks) - 5} more tasks*")
        
        st.divider()

# Load tasks on startup
load_tasks()

# Auto-move incomplete tasks
move_incomplete_tasks()

# Main UI
st.title("📅 Task Calendar")

# View mode toggle
col1, col2 = st.columns([3, 1])
with col2:
    view_mode = st.selectbox("View Mode", ["daily", "weekly"], 
                            index=0 if st.session_state.view_mode == 'daily' else 1,
                            key="view_mode_select")
    if view_mode != st.session_state.view_mode:
        st.session_state.view_mode = view_mode
        st.rerun()

# Sidebar for adding tasks and calendar
with st.sidebar:
    st.header("Add New Task")
    
    # Date selection for new tasks
    if st.session_state.view_mode == 'daily':
        task_date = st.date_input("Date", value=st.session_state.selected_date)
    else:
        task_date = st.date_input("Date", value=datetime.now().date())
    
    date_str = task_date.strftime('%Y-%m-%d')
    
    # Task form
    with st.form("add_task_form"):
        task_title = st.text_input("Task Title*", placeholder="Enter task title...")
        task_description = st.text_area("Description (optional)", placeholder="Task details...")
        task_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
        
        submitted = st.form_submit_button("Add Task")
        
        if submitted and task_title:
            add_task(date_str, task_title, task_priority, task_description)
            st.success("Task added!")
            st.rerun()
        elif submitted and not task_title:
            st.error("Please enter a task title!")
    
    st.divider()
    
    # Calendar widget (only show in daily mode)
    if st.session_state.view_mode == 'daily':
        create_calendar_widget()
    
    # Quick navigation
    st.divider()
    st.subheader("🔍 Quick Navigation")
    
    if st.button("📍 Go to Today", use_container_width=True):
        st.session_state.selected_date = datetime.now().date()
        if st.session_state.view_mode == 'weekly':
            today = datetime.now().date()
            days_since_monday = today.weekday()
            st.session_state.selected_week_start = today - timedelta(days=days_since_monday)
        st.rerun()
    
    # Show recent dates with tasks
    st.write("**Recent dates with tasks:**")
    dates_with_tasks = sorted([date for date in st.session_state.tasks.keys() if st.session_state.tasks[date]], reverse=True)
    
    for date_str in dates_with_tasks[:5]:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            task_count = len(st.session_state.tasks[date_str])
            completed_count = sum(1 for task in st.session_state.tasks[date_str].values() if task['completed'])
            
            if st.button(f"{date_obj.strftime('%m/%d')} ({completed_count}/{task_count})", 
                        key=f"nav_{date_str}", use_container_width=True):
                st.session_state.selected_date = date_obj
                if st.session_state.view_mode == 'weekly':
                    days_since_monday = date_obj.weekday()
                    st.session_state.selected_week_start = date_obj - timedelta(days=days_since_monday)
                st.rerun()
        except ValueError:
            continue

# Main content area
if st.session_state.view_mode == 'daily':
    display_daily_tasks()
else:
    display_weekly_tasks()

# Statistics
st.sidebar.divider()
st.sidebar.subheader("📊 Statistics")

total_tasks = sum(len(tasks) for tasks in st.session_state.tasks.values())
completed_tasks = sum(1 for tasks in st.session_state.tasks.values() 
                     for task in tasks.values() if task['completed'])

if total_tasks > 0:
    completion_rate = (completed_tasks / total_tasks) * 100
    st.sidebar.metric("Total Tasks", total_tasks)
    st.sidebar.metric("Completed", completed_tasks)
    st.sidebar.metric("Completion Rate", f"{completion_rate:.1f}%")
else:
    st.sidebar.info("No tasks yet!")

# Today's summary
today_str = datetime.now().date().strftime('%Y-%m-%d')
if today_str in st.session_state.tasks:
    today_tasks = st.session_state.tasks[today_str]
    today_total = len(today_tasks)
    today_completed = sum(1 for task in today_tasks.values() if task['completed'])
    
    st.sidebar.write("**Today's Progress:**")
    st.sidebar.progress(today_completed / today_total if today_total > 0 else 0)
    st.sidebar.write(f"{today_completed}/{today_total} completed")

# Data management
st.sidebar.divider()
st.sidebar.subheader("🔧 Data Management")

if st.sidebar.button("🔄 Manual Task Rollover"):
    move_incomplete_tasks()
    st.rerun()

if st.sidebar.button("💾 Export Data"):
    try:
        data_json = json.dumps(st.session_state.tasks, indent=2, default=str)
        st.sidebar.download_button(
            label="Download JSON",
            data=data_json,
            file_name=f"tasks_export_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    except Exception as e:
        st.sidebar.error(f"Export failed: {e}")

# Instructions
with st.expander("ℹ️ Cómo usar esta aplicación"):
    st.markdown("""
    **Modos de Vista:**
    - **Vista Diaria**: Enfócate en un día a la vez con calendario completo
    - **Vista Semanal**: Ve las tareas de toda la semana de una vez
    
    **Navegación:**
    - Usa el calendario visual para seleccionar fechas (Modo diario)
    - Usa los botones de navegación para las semanas (Modo semanal)
    - Acceso rápido a hoy y fechas recientes con tareas
    
    **Añadir Tareas:**
    - Usa el formulario de la barra lateral para añadir nuevas tareas
    - Establece prioridad: Alta (🔴), Media (🟡), Baja (🟢)
    - Las tareas se ordenan automáticamente por prioridad
    
    **Gestionar Tareas:**
    - Marca las casillas para completar tareas
    - Usa el botón ✏️ para editar tareas y moverlas entre fechas
    - Usa el botón 🗑️ para eliminar tareas
    - Las tareas incompletas se mueven automáticamente al día siguiente
    
    **Almacenamiento de Datos:**
    - **Localmente**: Las tareas se guardan automáticamente
    - **En línea**: Las tareas se mantienen durante la sesión del navegador
    - **Respaldos**: Descarga respaldos regulares para no perder datos
    
    **Características del Calendario:**
    - Los números en paréntesis muestran tareas (completadas/total)
    - 📍 indica la fecha de hoy
    - Las fechas seleccionadas están resaltadas
    """)

# Add a persistent storage warning for deployed environments
if 'storage_warning_shown' not in st.session_state:
    st.session_state.storage_warning_shown = True
    
    # Check if we're in a deployed environment (no file write access)
    try:
        with open('test_write.txt', 'w') as f:
            f.write('test')
        import os
        os.remove('test_write.txt')
        # We can write files - probably local
        local_env = True
    except:
        # Can't write files - probably deployed
        local_env = False
        
    if not local_env:
        st.error("""
        🚨 **AVISO CRÍTICO - App Desplegada en la Nube** 
        
        Tu app puede "dormirse" después de unas pocas horas de inactividad, perdiendo TODAS las tareas.
        
        **Soluciones inmediatas:**
        1. ✅ Activa "Auto-refrescar cada 10 minutos" en la barra lateral
        2. 💾 Descarga respaldos CADA VEZ que agregues tareas importantes
        3. 📱 Guarda el enlace en tu teléfono y ábrelo ocasionalmente
        
        **Para uso serio, considera:** migrar a una base de datos permanente
        """)

# Show backup reminder if user has tasks but auto-refresh is off
if st.session_state.tasks and not st.session_state.get('auto_refresh_enabled', False):
    st.warning("""
    ⚠️ **Recordatorio:** Tu app puede dormirse y perder las tareas. 
    
    **Opciones:** 
    - Activa "Auto-refrescar" en la barra lateral, O
    - Descarga un respaldo ahora mismo
    """)

# Emergency backup button in main area if lots of tasks
task_count = sum(len(tasks) for tasks in st.session_state.tasks.values())
if task_count > 15 and not st.session_state.get('auto_refresh_enabled', False):
    st.error(f"🚨 ¡Tienes {task_count} tareas sin protección automática!")
    
    backup_data = backup_tasks_to_browser()
    if backup_data:
        st.download_button(
            label="🚨 RESPALDO DE EMERGENCIA - DESCARGAR AHORA",
            data=backup_data,
            file_name=f"EMERGENCIA_tareas_{datetime.now().strftime('%d_%m_%Y_%H%M')}.json",
            mime="application/json",
            type="primary",
            use_container_width=True
        )

