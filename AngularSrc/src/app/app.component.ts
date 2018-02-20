import {Component, ElementRef, EventEmitter, Injectable, Input, Output} from '@angular/core';
import { Socket } from 'ngx-socket-io';
import {inherits} from "util";


class CoderPadSocket extends Socket{
  user_data = {};


  on_connect(cb:Function){
    this.on('connect',()=>cb())
  }
  join_room(roomname,username){
    this.user_data = {username:username,room:roomname}
    this.emit('join',this.user_data)
  }
  speak(message){
    this.emit('speak',{'message':message,
                                      'room_details':this.user_data})
  }
  sync_request(){
    this.emit('sync_request',{'room_details':this.user_data})
  }
  on_sync_result(cb:Function){
    this.user_data
    this.on('sync_result',(data)=>cb(data))
  }
  on_user_speech(cb:Function){
    this.on('user_speech',(data)=>cb(data))
  }
  on_user_joined(cb:Function){
    this.on('user_joined',(data)=>cb(data))
  }
  on_user_left(cb:Function){
    this.on('user_left',(data)=>cb(data))
  }
  on_user_list(cb:Function){
    this.on('user_list',(data)=>cb(data))
  }
  constructor(opts){
    super(opts);

  }

}
@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})


export class AppComponent {
  connect_to:{username:string,room:string,ws_url:string};
  private connection:CoderPadSocket;
  private _detail_container:{ws:any,room_details:any}={ws:{},room_details:{}};
  get details(){
    return this._detail_container
  }
  set details(val:{}){
    for(let key in val){
      console.log(key,"=",val[key]);
      this._detail_container[key]=val[key];
    }
  }
  get room_name(){
    return this._detail_container.room_details.room_name;
  }
  get username(){
    return this._detail_container.room_details.username;
  }
  set b64_context(val){
    this.details = JSON.parse(atob(val));
    console.log(this.details)
  }
  title = 'app';
  constructor(private elementRef:ElementRef){
    this.b64_context = this.elementRef.nativeElement.getAttribute('data-b64enc');

  }
  sync_request(){
    this.connection.sync_request()
  }
  send_handshake(){
    console.log("ATTEMPT TO JOIN ROOM!")
    this.connection.join_room(this.room_name,this.username)
  }
  on_user_joined(userDetails){
    this.connection.sync_request()
    console.log("Hello!:",userDetails)
  }
  on_user_list(userDetails){
    console.log("UserList",userDetails)
  }
  on_user_left(userDetails){
    console.log("GOODBYE:",userDetails)
    this.connection.sync_request()
  }
  on_sync_result(userDetails){
    console.log("??!")
    if (userDetails['active_users']) {
        this.details['room_details'].users=userDetails['active_users']
    }
    if(userDetails['program_text']) {
        this.details['editor_details'].current_text = userDetails['program_text']
    }else{
      this.details['editor_details'].current_text = "def test(x):"
    }

    console.log("GOT SYNC:",userDetails)
  }
  ngOnInit() {
    let url = this.details['ws'].url;
    let opts = {'path':this.details['ws'].endpoint}
    console.log(url,opts)
    this.connection = new CoderPadSocket({url:url,options:opts})
    this.connection.on_connect(()=>this.send_handshake());
    this.connection.on_user_joined((userDetails)=>this.on_user_joined(userDetails))
    this.connection.on_user_list((userDetails)=>this.on_user_list(userDetails))
    this.connection.on_user_left((userDetails)=>this.on_user_left(userDetails))
    this.connection.on_sync_result((userDetails)=>this.on_sync_result(userDetails))
    console.log("DDDDD",url)
    // console.log("CCCCC",this.connect_to)
    // let connection_info:{username:string,room:string} = JSON.parse(atob(this.connect_to))
    // console.log(connection_info)
  }

}
