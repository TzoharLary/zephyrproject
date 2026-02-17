#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

void central_main(void)
{
    int i = 0;
    while(1) {
        printk("Central running... %d\n", i++);
        k_sleep(K_SECONDS(1));
    }
}
