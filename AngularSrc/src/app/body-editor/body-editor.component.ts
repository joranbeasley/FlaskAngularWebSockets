import {Component, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
import {AceEditorComponent, AceEditorDirective} from "ng2-ace-editor";

@Component({
  selector: 'app-body-editor',
  templateUrl: './body-editor.component.html',
  styleUrls: ['./body-editor.component.scss']
})
export class BodyEditorComponent implements OnInit {
  editor_text = '';
  editor_options= {};//basePath:'/lib/ace',modePath:'/lib/ace2',themePath:'/lib/ace3'};
  editor_theme= 'eclipse';
  editor_language= 'python';
  editMgr;
  _details={}

  @Input()
  get details(){
    return this._details;
  }
  @Output() detailsChange = new EventEmitter();
  set details(val:{}){
    if(!val){return;}
    console.log("OK?",val)
    this._details = val;
    this.editor_text = val['editor_text']? val['editor_text']:'';
    this.editor_options = val['editor_options']? val['editor_options']:{};
    this.editor_theme = val['theme']? val['theme']:'monokai';
    this.editor_language = val['language']? val['language']:'python';
    this.detailsChange.emit(this._details);
  }
  constructor() {
    this.editMgr=this;
  }
  onEditorChange(){
    console.log("OK?",this.editor_text,"ASDAS")
  }

  ngOnInit() {

  }

}
