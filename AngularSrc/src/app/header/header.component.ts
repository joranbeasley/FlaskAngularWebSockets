import {EventEmitter,Component, Input, OnInit, Output} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {HttpHeaders} from "@angular/common/http";
@Component({
    selector:'user-badge',
    templateUrl: './userbadge.widget.html',
    styleUrls: ['./userbadge.widget.scss']
})
export class UserBadge implements OnInit {
  @Input() user;
  @Input() is_admin;

  ngOnInit() {
    console.log("User Badge?:",this.user,'a',this.is_admin,'b')
  }
}
@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss']
})
export class HeaderComponent implements OnInit {
  editMgr={"editor_language":"python"}
  language_options= ['python', 'javascript', 'django', 'c_cpp', 'sh', 'php', 'html', 'sql', 'typescript', 'lisp', 'fortran'];
  theme_options= ['monokai', 'eclipse', 'sunburst', 'clouds', 'twilight', 'dawn', 'crimson', 'sql', 'typescript', 'lisp', 'fortran'];
  selected_user = null;
  _details:{ws:any,room_details:{room_owner: boolean,room_name: string,users:any[]},editor_details:{}};
  new_candidate = {nickname:"",email:"",real_name:""};
  @Input()
  get details(){
    return this._details;
  }
  @Output() detailsChange = new EventEmitter();
  set details(val){
    this._details = val;
    this.detailsChange.emit(this._details);
  }

  room_owner():boolean{
    return this.details.room_details.room_owner;
  }
  room_name():string{
    return this.details.room_details.room_name;
  }
  constructor(private $http:HttpClient) { }
  onInviteCandidate(){
    console.log("INVITE!!!", this.new_candidate,this.$http)
    this.new_candidate['room_name'] = this.room_name()

    this.$http.post("/admin/invite_guest",this.new_candidate).subscribe(
      (result)=>this.onCandidateInvitationSuccess(result),
      (err)=>console.log("EEE:",err)
    )
  }
  getUserClasses(user){
    if(this.room_owner()){
      let s = "admin ";
      s += user.state?user.state:"";
      s += user.is_admin?" is_admin":"";
      return s
    }
    return ""
  }
  onCandidateInvitationSuccess(result){
    this.new_candidate = {nickname:"",email:"",real_name:""};
    console.log("R:",result)
    this.details.room_details.users.push(result)
    console.log("ADDED USER:",this.details.room_details)
  }
  onUpdateInvitee(){
    console.log("RN:",this.new_candidate.real_name)
    this.new_candidate.nickname = this.new_candidate.real_name.split(" ",2)[0]
  }
  onSelectLanguage() {
    console.log("LANG:", this.editMgr.editor_language);
  }
  ngOnInit() {
    console.log("GOT DEETS?:",this.details)
  }
}
