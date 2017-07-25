import { NgModule }      from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent }  from './app.component';
import {Routes, RouterModule} from "@angular/router";
import {IndexComponent} from "./index.component";
import {Http, HttpModule} from "@angular/http";
import {ResourceListComponent} from "./resource_list.component";
import {FormsModule} from "@angular/forms";
import {PaginationComponent} from "./pagination.component";

const appRoutes: Routes = [
  {
    path: '', component: IndexComponent
  }, {
    path: 'resource/:name', component: ResourceListComponent
  }
];

@NgModule({
  imports:      [
    BrowserModule,
    HttpModule,
    FormsModule,
    RouterModule.forRoot(
      appRoutes,
      {enableTracing: false, useHash: true}
    )
  ],
  declarations: [
    AppComponent ,
    IndexComponent,
    ResourceListComponent,
    PaginationComponent
  ],
  bootstrap:    [ AppComponent ]
})
export class AppModule { }
