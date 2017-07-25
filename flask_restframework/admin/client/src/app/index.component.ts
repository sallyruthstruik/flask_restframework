/**
 * Created by stas on 25.07.17.
 */

import {Component, OnInit} from '@angular/core';
import {ResourceInfo, BackendService} from "./backend.service";

@Component({
  selector: 'index',
  template: `
<ul>
  <li *ngFor="let res of resources"><a routerLink="/resource/{{res.name}}">{{res.name}}</a> </li>
</ul>
`,
  providers: [BackendService]
})
export class IndexComponent implements OnInit{

  ngOnInit(): void {
    this.backendService.getResourceInfo()
      .then(resources=>{
        this.resources=resources;
      });
  }

  constructor(private backendService: BackendService){}

  resources: ResourceInfo[];
}
