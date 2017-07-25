/**
 * Created by stas on 25.07.17.
 */

import {Injectable} from "@angular/core";
import {Http} from "@angular/http";
import {Constants} from "./constants";
import 'rxjs/add/operator/toPromise';

export interface ResourceInfo{
  name: string,
  url: string
}

@Injectable()
export class BackendService{

  constructor(private http: Http){}

  resourcesInfo: ResourceInfo[];

  getResourceInfo(): Promise<ResourceInfo[]>{
    if(this.resourcesInfo)
      return Promise.resolve(this.resourcesInfo);

    return this.http.get(`${Constants.HOST}/admin/resources`)
      .toPromise()
      .then(response=>{
        this.resourcesInfo = response.json();
        return this.resourcesInfo;
      })
      .catch(this.handleError)
  }

  handleError(err: any){
    console.log("ERROR", err);
  }

  /**
   * Возвращает данные с ресурса
   * @param name
   */
  getDataFromResource(name: string, filters: any, ordering: string[]): Promise<any> {

    let prepareFilters: string[] = [];

    for(let key of Object.keys(filters)){
      prepareFilters.push(`${key}=${encodeURIComponent(filters[key])}`)
    }

    console.log("Get data from resource", name);
    return this.getResourceInfo().then(
      response=>response.filter(item=>item.name == name)[0]
    ).then(
      resourceItem=>this.http.get(
        `${Constants.HOST}${resourceItem.url}?ordering=${ordering.join(",")}&${prepareFilters.join("&")}`
      ).toPromise()
    ).then(
      response=>response.json()
    ).catch(this.handleError)
  }
}
