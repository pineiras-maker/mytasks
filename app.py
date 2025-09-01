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

def edit_task(old_date_str, task_id, new_date_str, title, priority, description):
    """Edit a task and optionally move it to a different date"""
    if old_date_str in st.session_state.tasks and task_id in st.session_state.tasks[old_date_str]:
        # Get the existing task
        task = st.session_state.tasks[old_date_str][task_id].copy()
        
        # Update task details
        task['title'] = title
        task['priority'] = priority
        task['description'] = description
        task['modified_at'] = datetime.now().isoformat()
        
        # If moving to a different date
        if old_date_str != new_date_str:
            # Remove from old date
            del st.session_state.tasks[old_date_str][task_id]
            if not st.session_state.tasks[old_date_str]:
                del st.session_state.tasks[old_date_str]
            
            # Add to new date
            if new_date_str not in st.session_state.tasks:
                st.session_state.tasks[new_date_str] = {}
            st.session_state.tasks[new_date_str][task_id] = task
        else:
            # Just update in place
            st.session_state.tasks[old_date_str][task_id] = task
        
        save_tasks()

def format_date_spanish(date_obj):
    """Format date in Spanish format (DD/MM/YYYY)"""
    return date_obj.strftime('%d/%m/%Y')

def format_date_long_spanish(date_obj):
    """Format date in long Spanish format"""
    days_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    months_spanish = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    day_name = days_spanish[date_obj.weekday()]
    month_name = months_spanish[date_obj.month]
    
    return f"{day_name}, {date_obj.day} de {month_name} de {date_obj.year}"

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
        months_spanish = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        st.write(f"**{months_spanish[current_month]} {current_year}**")
    
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
    days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
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
    st.subheader(f"Tareas para {format_date_long_spanish(st.session_state.selected_date)}")
    
    tasks = get_sorted_tasks(date_str)
    
    if not tasks:
        st.info("No hay tareas para esta fecha. ¡Añade una tarea usando la barra lateral!")
    else:
        for task_id, task in tasks:
            with st.container():
                col_check, col_content, col_actions = st.columns([0.5, 4, 1])
                
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
                    priority_spanish = {'High': 'Alta', 'Medium': 'Media', 'Low': 'Baja'}.get(task['priority'], task['priority'])
                    
                    st.markdown(f"""
                    <div style="{title_style}">
                        {priority_icon} <strong>{task['title']}</strong>
                        <br><small>Prioridad: {priority_spanish}</small>
                        {f"<br><em>{task['description']}</em>" if task['description'] else ""}
                        {'<br><small>📁 Movida desde día anterior</small>' if task.get('moved_from') else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_actions:
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{task_id}", help="Editar tarea"):
                            st.session_state[f'editing_{task_id}'] = True
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"del_{task_id}", help="Eliminar tarea"):
                            delete_task(date_str, task_id)
                            st.rerun()
                
                # Edit form (appears when edit button is clicked)
                if st.session_state.get(f'editing_{task_id}', False):
                    with st.form(key=f"edit_form_{task_id}"):
                        st.write("**Editar Tarea:**")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_title = st.text_input("Título", value=task['title'], key=f"edit_title_{task_id}")
                            edit_priority = st.selectbox("Prioridad", ["High", "Medium", "Low"], 
                                                       index=["High", "Medium", "Low"].index(task['priority']),
                                                       format_func=lambda x: {'High': 'Alta', 'Medium': 'Media', 'Low': 'Baja'}[x],
                                                       key=f"edit_priority_{task_id}")
                        with col2:
                            edit_date = st.date_input("Mover a fecha", 
                                                    value=st.session_state.selected_date, 
                                                    key=f"edit_date_{task_id}")
                            edit_description = st.text_area("Descripción", 
                                                           value=task.get('description', ''), 
                                                           key=f"edit_desc_{task_id}")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Guardar", use_container_width=True):
                                new_date_str = edit_date.strftime('%Y-%m-%d')
                                edit_task(date_str, task_id, new_date_str, edit_title, edit_priority, edit_description)
                                st.session_state[f'editing_{task_id}'] = False
                                # Update selected date if task was moved
                                if new_date_str != date_str:
                                    st.session_state.selected_date = edit_date
                                st.success("¡Tarea actualizada!")
                                st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f'editing_{task_id}'] = False
                                st.rerun()
                
                st.divider()

def display_weekly_tasks():
    """Display tasks for selected week"""
    week_start = st.session_state.selected_week_start
    week_end = week_start + timedelta(days=6)
    
    st.subheader(f"Semana del {format_date_spanish(week_start)} - {format_date_spanish(week_end)}")
    
    # Week navigation
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("◀ Semana Anterior", key="prev_week"):
            st.session_state.selected_week_start -= timedelta(days=7)
            st.rerun()
    with col3:
        if st.button("Siguiente Semana ▶", key="next_week"):
            st.session_state.selected_week_start += timedelta(days=7)
            st.rerun()
    
    # Display each day of the week
    days_spanish = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    for i in range(7):
        current_day = week_start + timedelta(days=i)
        date_str = current_day.strftime('%Y-%m-%d')
        day_name = days_spanish[i]
        formatted_date = format_date_spanish(current_day)
        
        # Day header
        is_today = current_day == datetime.now().date()
        header_text = f"**{day_name}, {formatted_date}**"
        if is_today:
            header_text += " 📍"
        
        st.markdown(header_text)
        
        # Tasks for this day
        tasks = get_sorted_tasks(date_str)
        
        if not tasks:
            st.markdown("*Sin tareas*")
        else:
            # Create columns for tasks
            for task_id, task in tasks[:5]:  # Show max 5 tasks per day in weekly view
                col_check, col_content, col_actions = st.columns([0.3, 4, 0.5])
                
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
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"week_edit_{task_id}", help="Editar tarea"):
                            st.session_state[f'editing_{task_id}'] = True
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"week_del_{task_id}", help="Eliminar tarea"):
                            delete_task(date_str, task_id)
                            st.rerun()
                
                # Edit form for weekly view
                if st.session_state.get(f'editing_{task_id}', False):
                    with st.form(key=f"week_edit_form_{task_id}"):
                        st.write("**Editar Tarea:**")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_title = st.text_input("Título", value=task['title'], key=f"week_edit_title_{task_id}")
                            edit_priority = st.selectbox("Prioridad", ["High", "Medium", "Low"], 
                                                       index=["High", "Medium", "Low"].index(task['priority']),
                                                       format_func=lambda x: {'High': 'Alta', 'Medium': 'Media', 'Low': 'Baja'}[x],
                                                       key=f"week_edit_priority_{task_id}")
                        with col2:
                            edit_date = st.date_input("Mover a fecha", 
                                                    value=current_day, 
                                                    key=f"week_edit_date_{task_id}")
                            edit_description = st.text_area("Descripción", 
                                                           value=task.get('description', ''), 
                                                           key=f"week_edit_desc_{task_id}")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Guardar", use_container_width=True):
                                new_date_str = edit_date.strftime('%Y-%m-%d')
                                edit_task(date_str, task_id, new_date_str, edit_title, edit_priority, edit_description)
                                st.session_state[f'editing_{task_id}'] = False
                                st.success("¡Tarea actualizada!")
                                st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f'editing_{task_id}'] = False
                                st.rerun()
            
            # Show "and X more" if there are more tasks
            if len(tasks) > 5:
                st.markdown(f"*... y {len(tasks) - 5} tareas más*")
        
        st.divider()

# Load tasks on startup
load_tasks()

# Auto-move incomplete tasks
move_incomplete_tasks()

# Main UI
st.title("📅 Calendario de Tareas")

# View mode toggle
col1, col2 = st.columns([3, 1])
with col2:
    view_mode = st.selectbox("Modo de Vista", ["daily", "weekly"], 
                            index=0 if st.session_state.view_mode == 'daily' else 1,
                            format_func=lambda x: "Diario" if x == "daily" else "Semanal",
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
with st.expander("ℹ️ How to use this app"):
    st.markdown("""
    **View Modes:**
    - **Daily View**: Focus on one day at a time with full calendar widget
    - **Weekly View**: See an entire week's tasks at once
    
    **Navigation:**
    - Use the visual calendar to select dates (Daily mode)
    - Use navigation buttons for weeks (Weekly mode)
    - Quick access to today and recent dates with tasks
    
    **Adding Tasks:**
    - Use the sidebar form to add new tasks
    - Set priority: High (🔴), Medium (🟡), Low (🟢)
    - Tasks are automatically sorted by priority
    
    **Managing Tasks:**
    - Check boxes to mark tasks as completed
    - Use 🗑️ button to delete tasks
    - Incomplete tasks automatically move to the next day
    
    **Calendar Features:**
    - Numbers in parentheses show (completed/total) tasks
    - 📍 indicates today's date
    - Selected dates are highlighted
    """)
