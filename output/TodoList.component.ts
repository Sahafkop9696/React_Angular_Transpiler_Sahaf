import { Component } from '@angular/core';

@Component({
  selector: 'app-todo-list',
  templateUrl: './TodoList.component.html',
  styleUrls: ['./TodoList.component.css']
})
export class TodoListComponent {
  todos: string[] = ['Learn React', 'Build a transpiler'];
  newTodo: string = '';

  addTodo() {
    if (this.newTodo.trim()) {
      this.todos = [...this.todos, this.newTodo];
      this.newTodo = '';
    }
  }
}
