import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import {HeaderComponent, UserBadge} from './header/header.component';
import { BodyComponent } from './body/body.component';
import { BodyEditorComponent } from './body-editor/body-editor.component';
import { BodyTerminalComponent } from './body-terminal/body-terminal.component';
import { BodyChatComponent } from './body-chat/body-chat.component';
import { AceEditorModule } from 'ng2-ace-editor';
import {FormsModule} from "@angular/forms";
import {HttpClientModule} from "@angular/common/http";
import { SocketIoModule, SocketIoConfig } from 'ngx-socket-io';

const config: SocketIoConfig = { url: 'http://localhost:5678', options: {} };


@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    BodyComponent,
    BodyEditorComponent,
    BodyTerminalComponent,
    UserBadge,
    BodyChatComponent
  ],
  imports: [
    BrowserModule,
    AceEditorModule,
    FormsModule,
    HttpClientModule,
    SocketIoModule.forRoot(config)

  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
