.class public final Lcom/uvp/Screensaver;
.super Ljava/lang/Object;
.source "Screensaver.java"

# interfaces
.implements Ljava/lang/Runnable;

# Original code injected by this patcher (not vendor code).
#
# Stand-in for the Viewpoint's screen-off: after the app's idle timeout a black
# overlay covers the window at minimum brightness (AMOLED pixels are off). The
# first touch wakes it and is swallowed, so it can't press anything underneath.
# The app's own wake-ups (ring, locate, remote view) wake it too, and it stays
# awake while the call view is showing.


# static fields
.field private static sActivity:Landroid/app/Activity;

.field private static sEnabled:Z

.field private static sAsleep:Z

.field private static sBusy:Z

.field private static sHandler:Landroid/os/Handler;

.field private static sOverlay:Landroid/view/View;

.field private static sReschedule:Lcom/uvp/Screensaver;

.field private static sSleep:Lcom/uvp/Screensaver;

.field private static sSwallow:Z

.field private static volatile sTimeoutMs:I

.field private static sWake:Lcom/uvp/Screensaver;


# instance fields
.field private final what:I


# direct methods
.method static constructor <clinit>()V
    .locals 1

    # default until the app applies its own screen timeout (60 s, like the app)
    const v0, 0xea60

    sput v0, Lcom/uvp/Screensaver;->sTimeoutMs:I

    const/4 v0, 0x1

    sput-boolean v0, Lcom/uvp/Screensaver;->sEnabled:Z

    return-void
.end method

.method public static isEnabled()Z
    .locals 1

    sget-boolean v0, Lcom/uvp/Screensaver;->sEnabled:Z

    return v0
.end method

.method public static setEnabled(Z)V
    .locals 3

    sput-boolean p0, Lcom/uvp/Screensaver;->sEnabled:Z

    # persist
    sget-object v0, Lcom/uvp/Screensaver;->sActivity:Landroid/app/Activity;

    if-eqz v0, :skip_persist

    const-string v1, "uvp_prefs"

    const/4 v2, 0x0

    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v1, "ss_enabled"

    invoke-interface {v0, v1, p0}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V

    :skip_persist
    if-eqz p0, :disabled

    invoke-static {}, Lcom/uvp/Screensaver;->schedule()V

    goto :done

    :disabled
    invoke-static {}, Lcom/uvp/Screensaver;->wake()V

    :done
    return-void
.end method

.method private constructor <init>(I)V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput p1, p0, Lcom/uvp/Screensaver;->what:I

    return-void
.end method

.method public static attach(Landroid/app/Activity;)V
    .locals 4

    sput-object p0, Lcom/uvp/Screensaver;->sActivity:Landroid/app/Activity;

    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    sput-object v0, Lcom/uvp/Screensaver;->sHandler:Landroid/os/Handler;

    new-instance v0, Lcom/uvp/Screensaver;

    const/4 v1, 0x0

    invoke-direct {v0, v1}, Lcom/uvp/Screensaver;-><init>(I)V

    sput-object v0, Lcom/uvp/Screensaver;->sSleep:Lcom/uvp/Screensaver;

    new-instance v0, Lcom/uvp/Screensaver;

    const/4 v1, 0x1

    invoke-direct {v0, v1}, Lcom/uvp/Screensaver;-><init>(I)V

    sput-object v0, Lcom/uvp/Screensaver;->sWake:Lcom/uvp/Screensaver;

    new-instance v0, Lcom/uvp/Screensaver;

    const/4 v1, 0x2

    invoke-direct {v0, v1}, Lcom/uvp/Screensaver;-><init>(I)V

    sput-object v0, Lcom/uvp/Screensaver;->sReschedule:Lcom/uvp/Screensaver;

    # full-window black overlay, hidden until sleep
    new-instance v0, Landroid/view/View;

    invoke-direct {v0, p0}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    const/high16 v1, -0x1000000

    invoke-virtual {v0, v1}, Landroid/view/View;->setBackgroundColor(I)V

    const/16 v1, 0x8

    invoke-virtual {v0, v1}, Landroid/view/View;->setVisibility(I)V

    sput-object v0, Lcom/uvp/Screensaver;->sOverlay:Landroid/view/View;

    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    move-result-object v1

    invoke-virtual {v1}, Landroid/view/Window;->getDecorView()Landroid/view/View;

    move-result-object v1

    check-cast v1, Landroid/view/ViewGroup;

    new-instance v2, Landroid/view/ViewGroup$LayoutParams;

    const/4 v3, -0x1

    invoke-direct {v2, v3, v3}, Landroid/view/ViewGroup$LayoutParams;-><init>(II)V

    invoke-virtual {v1, v0, v2}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    # load the saved screensaver-enabled flag (default true)
    const-string v0, "uvp_prefs"

    const/4 v1, 0x0

    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object v0

    const-string v1, "ss_enabled"

    const/4 v2, 0x1

    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z

    move-result v0

    sput-boolean v0, Lcom/uvp/Screensaver;->sEnabled:Z

    invoke-static {}, Lcom/uvp/Screensaver;->schedule()V

    return-void
.end method

.method public static onTouch(Landroid/view/MotionEvent;)Z
    .locals 3

    invoke-virtual {p0}, Landroid/view/MotionEvent;->getActionMasked()I

    move-result v0

    sget-boolean v1, Lcom/uvp/Screensaver;->sAsleep:Z

    if-eqz v1, :awake

    invoke-static {}, Lcom/uvp/Screensaver;->wake()V

    const/4 v1, 0x1

    sput-boolean v1, Lcom/uvp/Screensaver;->sSwallow:Z

    goto :swallow

    :awake
    sget-boolean v1, Lcom/uvp/Screensaver;->sSwallow:Z

    if-eqz v1, :pass

    # swallow the rest of the waking gesture, up to ACTION_UP / ACTION_CANCEL
    :swallow
    const/4 v1, 0x1

    if-eq v0, v1, :end_swallow

    const/4 v2, 0x3

    if-eq v0, v2, :end_swallow

    return v1

    :end_swallow
    const/4 v2, 0x0

    sput-boolean v2, Lcom/uvp/Screensaver;->sSwallow:Z

    return v1

    :pass
    invoke-static {}, Lcom/uvp/Screensaver;->schedule()V

    const/4 v1, 0x0

    return v1
.end method

.method public static poke()V
    .locals 2

    # may be called off the main thread
    sget-object v0, Lcom/uvp/Screensaver;->sHandler:Landroid/os/Handler;

    if-eqz v0, :none

    sget-object v1, Lcom/uvp/Screensaver;->sWake:Lcom/uvp/Screensaver;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    :none
    return-void
.end method

.method private static schedule()V
    .locals 4

    sget-object v0, Lcom/uvp/Screensaver;->sHandler:Landroid/os/Handler;

    if-eqz v0, :done

    sget-object v1, Lcom/uvp/Screensaver;->sSleep:Lcom/uvp/Screensaver;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    sget-boolean v2, Lcom/uvp/Screensaver;->sEnabled:Z

    if-eqz v2, :done

    sget-boolean v2, Lcom/uvp/Screensaver;->sBusy:Z

    if-nez v2, :done

    sget v2, Lcom/uvp/Screensaver;->sTimeoutMs:I

    if-lez v2, :done

    int-to-long v2, v2

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    :done
    return-void
.end method

.method public static setBusy(Z)V
    .locals 0

    # true while the call view is showing: wake and don't sleep until it closes
    sput-boolean p0, Lcom/uvp/Screensaver;->sBusy:Z

    if-eqz p0, :idle

    invoke-static {}, Lcom/uvp/Screensaver;->wake()V

    return-void

    :idle
    invoke-static {}, Lcom/uvp/Screensaver;->schedule()V

    return-void
.end method

.method private static setBrightness(F)V
    .locals 2

    sget-object v0, Lcom/uvp/Screensaver;->sActivity:Landroid/app/Activity;

    if-eqz v0, :none

    invoke-virtual {v0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    move-result-object v0

    invoke-virtual {v0}, Landroid/view/Window;->getAttributes()Landroid/view/WindowManager$LayoutParams;

    move-result-object v1

    iput p0, v1, Landroid/view/WindowManager$LayoutParams;->screenBrightness:F

    invoke-virtual {v0, v1}, Landroid/view/Window;->setAttributes(Landroid/view/WindowManager$LayoutParams;)V

    :none
    return-void
.end method

.method public static setTimeoutMs(I)V
    .locals 2

    # the app's screen timeout (ms); <= 0 means never sleep. May be off the main thread.
    sput p0, Lcom/uvp/Screensaver;->sTimeoutMs:I

    sget-object v0, Lcom/uvp/Screensaver;->sHandler:Landroid/os/Handler;

    if-eqz v0, :none

    sget-object v1, Lcom/uvp/Screensaver;->sReschedule:Lcom/uvp/Screensaver;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    :none
    return-void
.end method

.method private static sleep()V
    .locals 2

    sget-boolean v0, Lcom/uvp/Screensaver;->sBusy:Z

    if-nez v0, :skip

    sget-object v0, Lcom/uvp/Screensaver;->sOverlay:Landroid/view/View;

    if-eqz v0, :skip

    const/4 v1, 0x1

    sput-boolean v1, Lcom/uvp/Screensaver;->sAsleep:Z

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/view/View;->setVisibility(I)V

    invoke-virtual {v0}, Landroid/view/View;->bringToFront()V

    # 0.0f = minimum brightness
    const/4 v0, 0x0

    invoke-static {v0}, Lcom/uvp/Screensaver;->setBrightness(F)V

    :skip
    return-void
.end method

.method private static wake()V
    .locals 2

    const/4 v0, 0x0

    sput-boolean v0, Lcom/uvp/Screensaver;->sAsleep:Z

    sget-object v0, Lcom/uvp/Screensaver;->sOverlay:Landroid/view/View;

    if-eqz v0, :no_overlay

    const/16 v1, 0x8

    invoke-virtual {v0, v1}, Landroid/view/View;->setVisibility(I)V

    :no_overlay
    # -1.0f = back to the system brightness
    const/high16 v0, -0x40800000

    invoke-static {v0}, Lcom/uvp/Screensaver;->setBrightness(F)V

    invoke-static {}, Lcom/uvp/Screensaver;->schedule()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 2

    iget v0, p0, Lcom/uvp/Screensaver;->what:I

    if-nez v0, :not_sleep

    invoke-static {}, Lcom/uvp/Screensaver;->sleep()V

    return-void

    :not_sleep
    const/4 v1, 0x1

    if-ne v0, v1, :reschedule

    invoke-static {}, Lcom/uvp/Screensaver;->wake()V

    return-void

    :reschedule
    invoke-static {}, Lcom/uvp/Screensaver;->schedule()V

    return-void
.end method
