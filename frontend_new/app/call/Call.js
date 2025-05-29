import { useCallback } from 'react';
import Image from "next/image";
import styles from './call.module.css';


export function Call({ data, onClose }) {

    const onButtonContainerClick = useCallback(() => {
        onClose();
    }, []);

    return (
        <div className={styles.callMainContainer}>
            <div className={styles.live}>
                <div className={styles.titleParent}>
                    <b className={styles.title}>{data.summaryTitle}</b>
                    <div className={styles.callInfoHeader}>
                        <div className={styles.div}>{data.identifier}</div>
                        <div className={styles.div}>•</div>
                        <div className={styles.div}>00 m 47s</div>
                    </div>
                </div>
                <Image className={styles.barChartIcon} width={36} height={36} sizes="100vw" alt="" src="call_wave.svg" />
            </div>
            <div className={styles.frameParent}>
                <div className={styles.frameGroup}>
                    <div className={styles.frameContainer}>
                        <div className={styles.markSmithParent}>
                            <div className={styles.div}>Mark Smith</div>
                            <div className={styles.div}>•</div>
                            <div className={styles.div}>11:26:17 AM</div>
                        </div>
                        <div className={styles.largeButton}>
                            <div className={styles.iTriedBut}>I tried, but I never got the reset email.</div>
                        </div>
                    </div>
                    <div className={styles.frameDiv}>
                        <div className={styles.markSmithParent}>
                            <div className={styles.div}>Ava Sterling</div>
                            <div className={styles.div}>•</div>
                            <div className={styles.div}>11:26:23 AM</div>
                        </div>
                        <div className={styles.largeButton1}>
                            <div className={styles.iTriedBut}>
                                <p className={styles.gotItIll}>{`Got it. I’ll check if your email is `}</p>
                                <p className={styles.gotItIll}>{`blocked or mistyped in the system. `}</p>
                                <p className={styles.gotItIll}>{`Can you please confirm the email `}</p>
                                <p className={styles.gotItIll}>address linked to your account?</p>
                            </div>
                        </div>
                    </div>
                    <div className={styles.frameContainer}>
                        <div className={styles.markSmithParent}>
                            <div className={styles.div}>Mark Smith</div>
                            <div className={styles.div}>•</div>
                            <div className={styles.div}>11:26:36 AM</div>
                        </div>
                        <div className={styles.largeButton}>
                            <div className={styles.iTriedBut}>mark.smith@mycompany.com</div>
                        </div>
                    </div>
                    <div className={styles.frameDiv}>
                        <div className={styles.markSmithParent}>
                            <div className={styles.div}>Ava Sterling</div>
                            <div className={styles.div}>•</div>
                            <div className={styles.div}>11:26:41 AM</div>
                        </div>
                        <div className={styles.largeButton1}>
                            <div className={styles.iTriedBut}>
                                <p className={styles.gotItIll}>Your email is indeed blocked. I will</p>
                                <p className={styles.gotItIll}>unblock it now. Done. Try again please.</p>
                            </div>
                        </div>
                    </div>
                    <div className={styles.frameContainer}>
                        <div className={styles.markSmithParent}>
                            <div className={styles.div}>Mark Smith</div>
                            <div className={styles.div}>•</div>
                            <div className={styles.div}>11:26:50 AM</div>
                        </div>
                        <div className={styles.largeButton}>
                            <div className={styles.iTriedBut}>Works. Thanks.</div>
                        </div>
                    </div>
                    <div className={styles.frameDiv}>
                        <div className={styles.markSmithParent}>
                            <div className={styles.div}>Ava Sterling</div>
                            <div className={styles.div}>•</div>
                            <div className={styles.div}>11:26:55 AM</div>
                        </div>
                        <div className={styles.largeButton1}>
                            <div className={styles.iTriedBut}>Perfect, have a good day Mark.</div>
                        </div>
                    </div>
                    <div className={styles.frameWrapper}>
                        <div className={styles.markSmithParent}>
                            <div className={styles.div}>Call ended</div>
                            <div className={styles.div}>•</div>
                            <div className={styles.div}>11:27:01 AM</div>
                        </div>
                    </div>
                </div>
                <div className={styles.pause}>
                    <div className={styles.pauseInner}>
                        <div className={styles.groupDiv}>
                            <div className={styles.frameParent5}>
                                <div className={styles.frameChild} />
                                <div className={styles.frameChild} />
                            </div>
                            <Image className={styles.groupChild} width={407} height={22} sizes="100vw" alt="" src="call_wave.svg" />
                        </div>
                    </div>
                    <div className={styles.callDurationContainer}>00 m 47s</div>
                </div>
            </div>
            <div className={styles.buttonParent}>
                <div className={styles.button}>
                    <div className={styles.largeButton6}>
                        <div className={styles.background}>
                            <div className={styles.backgroundChild} />
                        </div>
                        <Image className={styles.gearIcon} width={20} height={20} sizes="100vw" alt="" src="call_settings.svg" />
                        <div className={styles.text}>
                            <b className={styles.manageCall}>Manage Call</b>
                        </div>
                    </div>
                </div>
                <div className={styles.button1} onClick={onButtonContainerClick}>
                    <div className={styles.button2}>
                        <div className={styles.largeButton6}>
                            <div className={styles.background}>
                                <div className={styles.backgroundItem} />
                            </div>
                            <Image className={styles.gearIcon} width={20} height={20} sizes="100vw" alt="" src="call_stop.svg" />
                            <div className={styles.text}>
                                <b className={styles.manageCall}>End Listening</b>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>);
};
