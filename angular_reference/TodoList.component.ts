
import { Component } from '@angular/core';

@Component({
  selector: 'app-todo-list',
  templateUrl: './TodoList.component.html',
  styleUrls: ['./TodoList.component.css']
})
export class TodoListComponent {
  todos: string[] = ['Learn Angular', 'Build a transpiler'];
  newTodo: string = '';

  addTodo() {
    if (this.newTodo.trim()) {
      this.todos.push(this.newTodo);
      this.newTodo = '';
    }
  }
}
