import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { BodyEditorComponent } from './body-editor.component';

describe('BodyEditorComponent', () => {
  let component: BodyEditorComponent;
  let fixture: ComponentFixture<BodyEditorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ BodyEditorComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(BodyEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });
});
