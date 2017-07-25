/**
 * Created by stas on 25.07.17.
 */
/**
 * Created by stas on 29.01.17.
 */
import {Component, Input} from '@angular/core';

@Component({
  selector: 'pagination',
  templateUrl: "app/pagination.component.html",

})
export class PaginationComponent  {

  @Input() page: number;
  @Input() pages: number;
  @Input() onPageSet: (page: number)=>null;

  getPages(): number[]{
    let minPage = Math.max(1, this.page - 3);
    let maxPage = Math.min(minPage + 5, this.pages+1);

    let out: number[] = [];
    while(minPage < maxPage){
      out.push(minPage++);
    }
    return out;
  }

  prevPage(){
    if(this.page > 1){
      this.page --;
      this.onPageSet(this.page);
    }
  }

  nextPage(){
    if(this.page < this.pages){
      this.page ++;
      this.onPageSet(this.page);
    }
  }

  goToPage(p: number){
    if(1 <= p && p <= this.pages) {
      this.page = p;
      this.onPageSet(this.page);
    }
  }

}
