package com.stuffwithstuff.magpie.intrinsic;

import com.stuffwithstuff.magpie.ast.Expr;
import com.stuffwithstuff.magpie.ast.pattern.Pattern;
import com.stuffwithstuff.magpie.interpreter.Callable;
import com.stuffwithstuff.magpie.interpreter.ClassObj;
import com.stuffwithstuff.magpie.interpreter.Context;
import com.stuffwithstuff.magpie.interpreter.Name;
import com.stuffwithstuff.magpie.interpreter.Obj;
import com.stuffwithstuff.magpie.interpreter.Scope;

/**
 * Built-in callable for creating an instance of some class. It relies on
 * "init()" to do the actual initialization. "new()" just creates a fresh
 * object and stores it where the "init()" built-in can find it.
 */
public class ClassNew implements Callable {
  public ClassNew(Scope closure) {
    mClosure = closure;
  }

  @Override
  public Obj invoke(Context context, Obj arg) {
    // Get the class being constructed.
    ClassObj classObj = arg.getField(0).asClass();
    return context.getInterpreter().constructNewObject(
        context, classObj, arg.getField(1));
  }
  
  @Override
  public Pattern getPattern() {
    // The receiver is any instance of Class, and it takes any argument, since
    // it will simply forward it onto 'init()'.
    return Pattern.record(
        Pattern.type(Expr.name(Name.CLASS)),
        Pattern.wildcard());
  }

  @Override
  public Scope getClosure() {
    return mClosure;
  }
  
  @Override
  public String getDoc() {
    return "Creates a new instance of a class.";
  }

  private final Scope mClosure;
}
