.class public final Lcom/uvp/SsSwitch;
.super Ljava/lang/Object;

# A self-contained "Screensaver" switch row, rendered with the app's own
# reusable switch-row composable (ui.settings.d0.r). Modelled on the app's
# existing Location-Thumbnails switch: remember { mutableStateOf(enabled) },
# then d0.r(label, checked, 0L, onToggle, composer, 0, 4). Not vendor code.

.method public static final Row(Landroidx/compose/runtime/k;)V
    .locals 15
    # p0 = composer (register v15)

    # remember { mutableStateOf(Screensaver.isEnabled()) }
    const v0, 0x5c0de01
    invoke-interface {p0, v0}, Landroidx/compose/runtime/k;->W(I)V

    invoke-interface {p0}, Landroidx/compose/runtime/k;->C()Ljava/lang/Object;
    move-result-object v0

    sget-object v1, Landroidx/compose/runtime/k;->a:Landroidx/compose/runtime/k$a;
    invoke-virtual {v1}, Landroidx/compose/runtime/k$a;->a()Ljava/lang/Object;
    move-result-object v1

    if-ne v0, v1, :cached

    invoke-static {}, Lcom/uvp/Screensaver;->isEnabled()Z
    move-result v2
    invoke-static {v2}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;
    move-result-object v2
    const/4 v3, 0x2
    const/4 v4, 0x0
    invoke-static {v2, v4, v3, v4}, Landroidx/compose/runtime/m4;->i(Ljava/lang/Object;Landroidx/compose/runtime/l4;ILjava/lang/Object;)Landroidx/compose/runtime/x1;
    move-result-object v0
    invoke-interface {p0, v0}, Landroidx/compose/runtime/k;->u(Ljava/lang/Object;)V

    :cached
    invoke-interface {p0}, Landroidx/compose/runtime/k;->P()V

    check-cast v0, Landroidx/compose/runtime/x1;

    # checked = state.getValue()  -> v7
    invoke-interface {v0}, Landroidx/compose/runtime/x4;->getValue()Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Ljava/lang/Boolean;
    invoke-virtual {v1}, Ljava/lang/Boolean;->booleanValue()Z
    move-result v7

    # onToggle lambda -> v10
    new-instance v10, Lcom/uvp/SsToggle;
    invoke-direct {v10, v0}, Lcom/uvp/SsToggle;-><init>(Landroidx/compose/runtime/x1;)V

    # d0.r(label, checked, 0L, onToggle, composer, 0, 4)
    const-string v6, "Screensaver"
    const-wide/16 v8, 0x0
    move-object v11, p0
    const/4 v12, 0x0
    const/4 v13, 0x4
    invoke-static/range {v6 .. v13}, Lcom/ui/da/viewer/app/ui/settings/d0;->r(Ljava/lang/String;ZJLfh/l;Landroidx/compose/runtime/k;II)V

    return-void
.end method
