import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BodyChatComponent } from './body-chat.component';

describe('BodyChatComponent', () => {
  let component: BodyChatComponent;
  let fixture: ComponentFixture<BodyChatComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BodyChatComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BodyChatComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
