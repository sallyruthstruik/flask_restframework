import {Component, OnInit} from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {BackendService} from "./backend.service";

@Component({
  selector: 'resource-list',
  templateUrl: "app/resource_list.components.html",
  providers: [BackendService]
})
export class ResourceListComponent implements OnInit{
  name: string;

  columns: string[] = [];
  filter_columns: string[] = [];

  ordering: string[] = [];
  data: any[];
  showFilters = false;

  filters: any = {
    country_code: "RU"
  };

  ngOnInit(): void {
    console.log("NgOnInit");
    this.route.params.subscribe(params=>{
      this.name = params["name"];
      this.fetchData();
    })
  }

  constructor(private route: ActivatedRoute, private backendService: BackendService){}

  fetchData(){
    console.log(this.filters);
    this.backendService.getDataFromResource(this.name, this.filters, this.ordering).then(
      data=>{
        this.data = data.results;
        return this.data;
      }
    ).then(
      this.fetchColumns
    ).then(
      this.fetchFilterColumns
    );
  }

  fetchColumns = ()=>{
    if(this.data.length > 0){
      this.columns = Object.keys(this.data[0])
    }
  };

  fetchFilterColumns = ()=>{
    if(this.data.length > 0){
      this.filter_columns = this.columns;
    }
  };

  changeOrdering = (col: string)=>{
    let reverseCol = `-${col}`;
    if(col[0] == "-"){
      reverseCol = col.slice(1, col.length);
    }

    if(this.ordering.indexOf(col) != -1){
      this.ordering = this.ordering.filter(i=>i!=col);
      this.ordering.push(reverseCol);
    }else if(this.ordering.indexOf(reverseCol) != -1){
      this.ordering = this.ordering.filter(i=>i!=reverseCol && i != col);
    }else{
      this.ordering.push(col);
    }

    this.fetchData();
  };

  onInputChange(column:string, e: any){
    this.filters[column] = e.target.value;
    console.log(column, e, e.target.value);
    this.showFilters = false;
    this.fetchData();
  }

}
/**
 * Created by stas on 25.07.17.
 */
