.class public final Lcom/uvp/SsToggle;
.super Ljava/lang/Object;
.implements Lfh/l;

# onCheckedChange for the injected "Screensaver" switch: update the Compose
# MutableState so the switch animates, and persist via Screensaver.setEnabled.
# Not vendor code.

.field private final s:Landroidx/compose/runtime/x1;

.method public constructor <init>(Landroidx/compose/runtime/x1;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/uvp/SsToggle;->s:Landroidx/compose/runtime/x1;
    return-void
.end method

.method public invoke(Ljava/lang/Object;)Ljava/lang/Object;
    .locals 2
    check-cast p1, Ljava/lang/Boolean;
    invoke-virtual {p1}, Ljava/lang/Boolean;->booleanValue()Z
    move-result v0

    iget-object v1, p0, Lcom/uvp/SsToggle;->s:Landroidx/compose/runtime/x1;
    invoke-static {v0}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;
    move-result-object p1
    invoke-interface {v1, p1}, Landroidx/compose/runtime/x1;->setValue(Ljava/lang/Object;)V

    invoke-static {v0}, Lcom/uvp/Screensaver;->setEnabled(Z)V

    sget-object p1, Lkotlin/y;->a:Lkotlin/y;
    return-object p1
.end method
