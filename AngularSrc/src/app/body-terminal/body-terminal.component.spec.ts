import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BodyTerminalComponent } from './body-terminal.component';

describe('BodyTerminalComponent', () => {
  let component: BodyTerminalComponent;
  let fixture: ComponentFixture<BodyTerminalComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BodyTerminalComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BodyTerminalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
