#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

void peripheral_main(void)
{
    int i = 0;
    while(1) {
        printk("Peripheral running... %d\n", i++);
        k_sleep(K_SECONDS(1));
    }
}
