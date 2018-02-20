import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';

@Component({
  selector: 'app-body',
  templateUrl: './body.component.html',
  styleUrls: ['./body.component.scss']
})
export class BodyComponent implements OnInit {
  _details={}

  @Input()
  get details(){
    return this._details;
  }
  @Output() detailsChange = new EventEmitter();
  set details(val){
    this._details = val;
    this.detailsChange.emit(this._details);
  }
  constructor() { }

  ngOnInit() {
    console.log("DETAILS:",this.details)
  }

}
