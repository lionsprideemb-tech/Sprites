# R23 native acceptance handoff — QA only

Do not put the isolated acceptance function into a playable ROM or enable it on a live PC or party screen. It deliberately writes scratch at texture and palette address zero. The default build always returns zero, without touching hardware.

## Reproduce host checks
From this directory:
```sh
gcc -std=c11 -Wall -Wextra -Werror -O2 -DR23_ISOLATED_HARNESS -DR23_HOST_MOCK r23_acceptance.c -o host && ./host
gcc -std=c11 -Wall -Wextra -Werror -O2 r23_acceptance.c r23_gate_test.c -o gate && ./gate
clang --target=arm-none-eabi -mcpu=arm946e-s -marm -ffreestanding -std=c11 -Wall -Wextra -Werror -O2 -c r23_acceptance.c -o gate_arm9.o
```

## Native prerequisite and next acceptance
Use the pinned pret/pokeplatinum source c248fb3f8cc9934ded800e489567c5c0eeee92eb and its declared NitroSDK eaae40f199c0a8827947afbc33227b6ba2f9d45c and NitroSystem 21c8fd078fdda34f3c2622ef0751d00adaacf890 dependencies. Follow its INSTALL.md and build configuration in a separately authorized, isolated SDK test project. No external private source upload, paid job, production build, or playable ROM modification. The SDK-specific compiler flags and startup/linker setup must be provided by the complete test project; they have not been executed here.

Compile r23_acceptance.c with R23_REAL_SDK and R23_ISOLATED_HARNESS only for the isolated test target, using its actual nitro.h. Invoke r23_acceptance(1) only in ARM9 system-mode after initialization, with displays and render tasks stopped and bank A plus palette banks F/G exclusively allocated to this test. No concurrent graphics/DMA users, even IRQ callbacks. Do not call from a live screen. Record return bits 1/2/4 (transfer returned, transfer returned, bank mappings restored). A value of 7 is a transfer smoke-test signal only: add independent readback and a rendered pixel oracle before native acceptance. No isolated native executable or SDK link has been verified.

## Engine integration gates
- PC: preserve preview allocation, original canonical OBJ icons and UI layers. Existing render hook is ov19_021D6474 before G3_SwapBuffers; VBlank and main column tasks are separate. No scratch harness call at either hook. Future approved icon transfer adapter must serialize with preview, own all DMA source bytes until EndLoad, and prove exclusive reservations.
- Party: after stock resource initialization, use the existing PlttTransfer_RequestFreeSpace allocator and actual palette proxy instead of hard-coded slots. Confirm task capacity, allocation bitmap, exact resource IDs and cleanup. The whole-range allocator ignores TryGetDestOffsets's false return; do not use it as a safe capacity oracle. Preserve existing shared cell and animation resources.
- Draw priority: main BG0 3D priority 1, BG1 priority 0, BG2 priority 1, BG3 priority 3. Moving OBJ icons to BG0 can change UI layering. Require real screen comparison for cursor, held item, preview, selection and scroll transitions.
- No new authoritative archive or registry evidence: keep nine missing historical binaries and 21 registry holds excluded. No repeat of completed pixel conversions or historical recovery probes without a new source.

## Exit condition
Real SDK-linked isolated diagnostic, real emulator/hardware execution, byte readback, screenshots/pixel comparison, complete reservation and priority checks. If unavailable, retain the offline handoff and continue only independent non-native project work.
