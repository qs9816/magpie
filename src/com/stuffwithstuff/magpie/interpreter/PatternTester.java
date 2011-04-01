package com.stuffwithstuff.magpie.interpreter;

import com.stuffwithstuff.magpie.ast.pattern.*;
import com.stuffwithstuff.magpie.parser.Position;
import com.stuffwithstuff.magpie.util.Pair;

/**
 * Determines if a pattern matches a given value.
 * 
 * @author bob
 */
public class PatternTester implements PatternVisitor<Boolean, Obj> {
  public static boolean test(final Interpreter interpreter, Pattern pattern,
      Obj value, EvalContext context) {
    
    PatternTester binder = new PatternTester(interpreter, context);
    return pattern.accept(binder, value);
  }
  
  @Override
  public Boolean visit(RecordPattern pattern, Obj value) {
    // Test each field.
    for (int i = 0; i < pattern.getFields().size(); i++) {
      Pair<String, Pattern> field = pattern.getFields().get(i);
      Obj fieldValue = mInterpreter.getQualifiedMember(
          Position.none(), value, mContext.getContainingClass(), field.getKey());
      if (!field.getValue().accept(this, fieldValue)) return false;
    }
    
    // If we got here, the fields all passed.
    return true;
  }

  @Override
  public Boolean visit(TuplePattern pattern, Obj value) {
    // Test each field.
    for (int i = 0; i < pattern.getFields().size(); i++) {
      Pattern fieldPattern = pattern.getFields().get(i);
      Obj field = mInterpreter.getQualifiedMember(
          Position.none(), value, mContext.getContainingClass(), Name.getTupleField(i));
      if (!fieldPattern.accept(this, field)) return false;
    }
    
    // If we got here, the fields all passed.
    return true;
  }

  @Override
  public Boolean visit(ValuePattern pattern, Obj value) {
    Obj expected = mInterpreter.evaluate(pattern.getValue(), mContext);
    
    return mInterpreter.objectsEqual(expected, value);
  }

  @Override
  public Boolean visit(VariablePattern pattern, Obj value) {
    // If we have a type for the variable, check it.
    if (pattern.getType() != null) {
      // TODO(bob): Should this be evaluated in the regular context even though
      // it's a type?
      Obj expected = mInterpreter.evaluate(pattern.getType(), mContext);
      
      // TODO(bob): Hack temp getting rid of types.
      if (!(expected instanceof ClassObj)) {
        throw new UnsupportedOperationException("should be class");
      }
      
      return value.getClassObj().isSubclassOf((ClassObj)expected);
    }
    
    // An untyped variable matches anything.
    return true;
  }

  private PatternTester(Interpreter interpreter, EvalContext context) {
    mInterpreter = interpreter;
    mContext = context;
  }
  
  private final Interpreter mInterpreter;
  private final EvalContext mContext;
}
